import os

from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Category, Word


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

                category_name = os.path.splitext(filename)[0]
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
        before_count = Word.objects.count()

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                if not line:
                    continue

                original, translation, transcription = line.split(';')

                word, _ = Word.objects.get_or_create(
                    word=original, 
                    translation=translation,
                    transcription=transcription)
                word.category.add(category)
                
        after_count = Word.objects.count()

        return after_count - before_count