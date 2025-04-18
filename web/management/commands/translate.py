import os

from django.core.management.base import BaseCommand

from deep_translator import GoogleTranslator
import eng_to_ipa as ipa
from tqdm import tqdm


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dirout_default = os.path.join(BASE_DIR, '..', '..', '..', 'wordlists', 'translated')


class Command(BaseCommand):
    help = 'Translate .txt words file'

    def add_arguments(self, parser):
        parser.add_argument('-i', '--input', required=True, help='Входной файл с английскими словами')
        parser.add_argument('-o', '--output', default=None, 
                       help='Выходной файл (по умолчанию: Такое же название как и входной файл')


    def handle(self, *args, **options):
        input_ = options['input']
        output_ = options['output']
        if not os.path.exists(input_):
            print(f"\nОшибка: входной файл '{input_}' не существует")
            return

        if not os.path.isfile(input_):
            print(f"\nОшибка: '{input_}' не является файлом")
            return

        if output_ == None:
            output_ = os.path.join(dirout_default, os.path.basename(input_))

        self.process_words(input_, output_)
        print(f'Saved to {os.path.abspath(output_)}')


    def translate_word(self, word):
        try:
            return GoogleTranslator(source='en', target='ru').translate(word)
        except:
            return None


    def get_transcription(self, word):
        try:
            return ipa.convert(word)
        except:
            return None


    def process_words(self, input_file, output_file):
        with open(input_file) as fin, open(output_file, 'w') as fout:
            words = fin.readlines()

            for word in tqdm(words, desc='Preparing the dictionary', colour='green'):
                word = word.strip()
                trans_word = self.translate_word(word)
                transcription = self.get_transcription(word)
                fout.write(f'{word};{trans_word};{transcription}\n')