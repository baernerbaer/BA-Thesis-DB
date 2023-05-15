# SR-MPP: Spaced Repetition Maintenance Practise Protocol
## What is this?

This is a small flashcard app written for my bachelor's thesis. It is targeted towards musicians and features a custom spaced-repetition algorithm.

## What features does it have?

Well, I'm glad you asked. Here's a list:

- attach any file (docx, pdf, ...) to your flashcard (e.g. music sheet) and open it with one button click when studying that card
- organise your decks with subdecks by dragging and dropping decks onto another
- always know when you created your card since this is shown when reviewing your card
- ..and well.. it uses a fancy algorithm

## Cool, how do I use this?

You will need Python3, PyQt6 (should be pre-installed with Python3) and [appdata](https://pypi.org/project/appdata/) to get it up and running.
To install the dependencies, open up a terminal and type:
```sh
pip install appdata PyQt6
```
You can then just run the `main.py` file and you're good to go!

### I use MacOS and want to be fancy

Well, you can create a `*.app` by first installing a few dependencies:
```sh
pip install appdata PyQt6 py2app
```

Then, run the following command:
```sh
python3 setup.py py2app
```

After a lot of terminal output, you will find your MacOS App (`Repetition.app`) in the generated `./dist` folder.

## License 

Copyright :copyright: 2023 David Buehler
