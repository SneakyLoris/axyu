import argparse
import os

from deep_translator import GoogleTranslator
import eng_to_ipa as ipa
from tqdm import tqdm


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dirout_default = os.path.join(BASE_DIR, '..', 'wordlists', 'translated')

def translate_word(word):
    try:
        return GoogleTranslator(source='en', target='ru').translate(word)
    except:
        return None


def get_transcription(word):
    try:
        return ipa.convert(word)
    except:
        return None


def process_words(input_file, output_file):
    with open(input_file) as fin, open(output_file, 'w') as fout:
        words = fin.readlines()

        for word in tqdm(words, desc='Preparing the dictionary', colour='green'):
            word = word.strip()
            trans_word = translate_word(word)
            transcription = get_transcription(word)
            fout.write(f'{word};{trans_word};{transcription}\n')


def main():
    parser = argparse.ArgumentParser(description='Перевод английских слов с транскрипцией')
    parser.add_argument('-i', '--input', required=True, help='Входной файл с английскими словами')
    parser.add_argument('-o', '--output', default=None, 
                       help='Выходной файл (по умолчанию: Такое же название как и входной файл')
    
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"\nОшибка: входной файл '{args.input}' не существует")
        return

    if not os.path.isfile(args.input):
        print(f"\nОшибка: '{args.input}' не является файлом")
        return
    
    output = args.output

    if args.output == None:
        output = os.path.join(dirout_default, os.path.basename(args.input))

    process_words(args.input, output)
    print(f'Saved to {os.path.abspath(output)}')
    
if __name__ == '__main__':
    main()