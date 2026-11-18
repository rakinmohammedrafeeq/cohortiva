import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from Users.models import Role, Faculty, Major


DEFAULT_ROLES = ['Student', 'Tutor', 'Admin']


class Command(BaseCommand):
    help = (
        "Idempotent command to seed reference data (Roles, and optionally approved "
        "Faculty and Major records). Uses database transactions and natural keys."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate execution and report changes without committing to the database.',
        )
        parser.add_argument(
            '--faculty-file',
            type=str,
            default=None,
            help='Path to approved faculty JSON file.',
        )
        parser.add_argument(
            '--major-file',
            type=str,
            default=None,
            help='Path to approved major JSON file.',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        faculty_file = options.get('faculty_file')
        major_file = options.get('major_file')

        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(self.style.MIGRATE_HEADING(f"{prefix}Starting reference data seeding..."))

        stats = {
            'roles_created': 0,
            'roles_existing': 0,
            'faculties_created': 0,
            'faculties_updated': 0,
            'faculties_existing': 0,
            'majors_created': 0,
            'majors_updated': 0,
            'majors_existing': 0,
        }

        try:
            with transaction.atomic():
                # 1. Seed Roles safely by natural key (name)
                self.stdout.write("--- Roles ---")
                for role_name in DEFAULT_ROLES:
                    role, created = Role.objects.get_or_create(name=role_name)
                    if created:
                        stats['roles_created'] += 1
                        self.stdout.write(f"  + Created Role: {role.name}")
                    else:
                        stats['roles_existing'] += 1
                        self.stdout.write(f"  = Existing Role: {role.name}")

                # 2. Seed Faculties if approved file provided
                if faculty_file:
                    if not os.path.exists(faculty_file):
                        self.stderr.write(self.style.ERROR(f"Faculty file not found: {faculty_file}"))
                    else:
                        self.stdout.write(f"--- Faculties (from {faculty_file}) ---")
                        with open(faculty_file, 'r', encoding='utf-8') as f:
                            faculties_data = json.load(f)

                        for item in faculties_data:
                            code = item.get('code', '').strip()
                            name = item.get('name', '').strip()
                            if not code or not name:
                                self.stdout.write(self.style.WARNING(f"  ! Skipping invalid faculty item: {item}"))
                                continue

                            faculty = Faculty.objects.filter(code=code).first()
                            if faculty is None:
                                Faculty.objects.create(code=code, name=name)
                                stats['faculties_created'] += 1
                                self.stdout.write(f"  + Created Faculty: [{code}] {name}")
                            elif faculty.name != name:
                                faculty.name = name
                                faculty.save(update_fields=['name'])
                                stats['faculties_updated'] += 1
                                self.stdout.write(f"  ~ Updated Faculty: [{code}] {name}")
                            else:
                                stats['faculties_existing'] += 1
                                self.stdout.write(f"  = Existing Faculty: [{code}] {name}")
                else:
                    self.stdout.write(self.style.NOTICE("No --faculty-file provided; skipping faculty seeding."))

                # 3. Seed Majors if approved file provided
                if major_file:
                    if not os.path.exists(major_file):
                        self.stderr.write(self.style.ERROR(f"Major file not found: {major_file}"))
                    else:
                        self.stdout.write(f"--- Majors (from {major_file}) ---")
                        with open(major_file, 'r', encoding='utf-8') as f:
                            majors_data = json.load(f)

                        for item in majors_data:
                            major_name = item.get('name', '').strip()
                            faculty_code = item.get('faculty_code')
                            faculty_id = item.get('faculty_id')

                            faculty = None
                            if faculty_code:
                                faculty = Faculty.objects.filter(code=faculty_code).first()
                            elif faculty_id:
                                faculty = Faculty.objects.filter(id=faculty_id).first()

                            if not faculty:
                                self.stdout.write(self.style.WARNING(
                                    f"  ! Skipping Major '{major_name}': Faculty not found (code={faculty_code}, id={faculty_id})"
                                ))
                                continue

                            major = Major.objects.filter(name=major_name).first()
                            if major is None:
                                Major.objects.create(name=major_name, faculty=faculty)
                                stats['majors_created'] += 1
                                self.stdout.write(f"  + Created Major: '{major_name}' -> Faculty [{faculty.code}]")
                            elif major.faculty_id != faculty.id:
                                major.faculty = faculty
                                major.save(update_fields=['faculty'])
                                stats['majors_updated'] += 1
                                self.stdout.write(f"  ~ Updated Major Faculty: '{major_name}' -> Faculty [{faculty.code}]")
                            else:
                                stats['majors_existing'] += 1
                                self.stdout.write(f"  = Existing Major: '{major_name}'")
                else:
                    self.stdout.write(self.style.NOTICE("No --major-file provided; skipping major seeding."))

                if dry_run:
                    transaction.set_rollback(True)
                    self.stdout.write(self.style.WARNING("\n[DRY-RUN] Changes rolled back. No database modifications were saved."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error during reference data seeding: {e}"))
            raise

        self.stdout.write("\n" + "=" * 45)
        self.stdout.write(self.style.SUCCESS(f"{prefix}Reference Data Seeding Summary:"))
        self.stdout.write(f"  Roles:     {stats['roles_created']} created, {stats['roles_existing']} existing")
        self.stdout.write(f"  Faculties: {stats['faculties_created']} created, {stats['faculties_updated']} updated, {stats['faculties_existing']} existing")
        self.stdout.write(f"  Majors:    {stats['majors_created']} created, {stats['majors_updated']} updated, {stats['majors_existing']} existing")
        self.stdout.write("=" * 45)
