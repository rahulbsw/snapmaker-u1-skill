"""Small hostile-input fixtures; no large allocations or command execution."""
import io
import unittest
from unittest import mock
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import xml.etree.ElementTree as ET

from scripts import u1_3mf as project


class ProjectInputTests(unittest.TestCase):
    def archive(self, names):
        data = io.BytesIO()
        with ZipFile(data, 'w', ZIP_DEFLATED) as archive:
            for name in names:
                member = ZipInfo()
                member.filename = name  # Preserve raw separators on Windows too.
                archive.writestr(member, b'fixture')
        return ZipFile(data)

    def test_ambiguous_unsafe_and_encrypted_members_are_rejected(self):
        for names in [['a', 'A'], ['../escape'], ['/absolute'], ['C:/escape'], ['C:escape'], ['Metadata\\bad'], ['bad\x00name']]:
            with self.subTest(names=names), self.archive(names) as archive:
                with self.assertRaises(ValueError):
                    project.validate_archive(archive)
        with self.archive(['safe']) as archive:
            archive.infolist()[0].flag_bits |= 1
            with self.assertRaisesRegex(ValueError, 'encrypted'):
                project.validate_archive(archive)

    def test_archive_limits_are_checked_before_reading(self):
        with self.archive(['a', 'b']) as archive, mock.patch.object(archive, 'open') as read:
            with mock.patch.object(project, 'MAX_MEMBERS', 1), self.assertRaises(ValueError):
                project.validate_archive(archive)
            archive.infolist()[0].file_size = project.MAX_MEMBER_BYTES + 1
            with self.assertRaisesRegex(ValueError, '512 MiB'):
                project.validate_archive(archive)
            archive.infolist()[0].file_size = 10
            with mock.patch.object(project, 'MAX_PROJECT_BYTES', 5), self.assertRaisesRegex(ValueError, '2 GiB'):
                project.validate_archive(archive)
            read.assert_not_called()

    def test_member_read_is_bounded_even_if_size_metadata_is_wrong(self):
        with self.archive(['a']) as archive:
            with mock.patch.object(archive, 'open') as read:
                with self.assertRaisesRegex(ValueError, 'read limit'):
                    project.read_member(archive, 'a', limit=2)
                read.assert_not_called()
                archive.infolist()[0].file_size = 1
                read.return_value.__enter__.return_value.read.return_value = b'123'
                with self.assertRaisesRegex(ValueError, 'read limit'):
                    project.read_member(archive, 'a', limit=2)
                read.return_value.__enter__.return_value.read.assert_called_once_with(3)

    def test_xml_doctypes_are_rejected_across_encodings(self):
        text = '<!DOCTYPE model [<!ENTITY x "benign">]><model>&x;</model>'
        for encoding in ['utf-8', 'utf-16', 'utf-16-be', 'utf-32']:
            with self.subTest(encoding=encoding), self.assertRaises((ValueError, ET.ParseError)):
                project.parse_xml(text.encode(encoding))
        self.assertEqual(project.parse_xml(b'<model/>').tag, 'model')

    def test_post_processing_requires_empty_well_formed_settings(self):
        for key in project.POST_PROCESS:
            for value in ['AUDIT_INERT_MARKER', ['AUDIT_INERT_MARKER'], 1, {}, [None]]:
                with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, 'Post-processing'):
                    project.reject_post_process({key: value})
            for value in [None, '', '  ', [], ['', ' ']]:
                project.reject_post_process({key: value})


if __name__ == '__main__':
    unittest.main()
