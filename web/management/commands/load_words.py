import os

from django.core.management.base import BaseCommand
from django.db import transaction
from web.models import Category, Word


class Command(BaseCommand):
    help = 'Insert words from all .txt files to database'

    def add_arguments(self, parser):
        parser.add_argument(
            'dir_path',
            type=str,
            help='Path to directory with .txt files'
        )


    def handle(self, *args, **options):
        dir_path = options['dir_path']

        if not os.path.isdir(dir_path):
            self.stderr.write(f"Directory not found: {dir_path}")
            return
        
        processed_files = 0
        total_words = 0

        with transaction.atomic():
            for filename in os.listdir(dir_path):
                if not filename.endswith('.txt'):
                    continue

                category_name = os.path.splitext(filename)[0].lower()
                file_path = os.path.join(dir_path, filename)

                category, _ = Category.objects.get_or_create(
                    name=category_name
                )

                words_added = self.process_file(file_path, category)
                total_words += words_added
                processed_files += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Processed {processed_files} files. "
                f"Added {total_words} words total."
            )
        )

    def process_file(self, file_path, category):
        words_to_create = []
        existing_words = set(
            Word.objects.filter(category=category)
            .values_list('word', flat=True)
        )

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                if not line:
                    continue

                original, translation, transcription = line.split(';')
                if original in existing_words:
                    continue
                words_to_create.append(Word(
                    word=original,
                    translation=translation,
                    transcription=transcription
                ))

        created_words = Word.objects.bulk_create(words_to_create)

        Word.category.through.objects.bulk_create([
            Word.category.through(word_id=word.id, category_id=category.id)
            for word in created_words
        ])

        return len(created_words)