## Audiobook generator that uses the Microsoft T5 Speech Transformer model from Huggingface to generate audiobooks from PDFs (NOTE: still under active development and experimentation, breaking changes were made recently, would not work now)

![alt text](./images/reading.jpeg)

## Introduction
Getting access to quality audio difficult is difficult or expensive, but access to pdf versions are relatively much easier. If you are someone whose always on the move having time to read pdf books can be unenjoyable and somtimes impossible. I am one of such people, so I decided to build an audio book generator using a text to speech model. 

## Structure
The project is mainly consists of the `main.py` file which contains the main executables and is the entry point of the application, and the `aiReader.py` which handles text cleaning and speech synthesizing.

## To run the application
To run the application you need to install the requirments using the following command. 

`pip install -r requirements.txt`

After successfully installing all the requirements, you can then run the application by specifying your input pdf file and you output mp3 file, here is an example command

`python main.py -i snowcrash.pdf -o snowcrash.mp3`

This would generate the audiobook for you, depending on the size of the audiobooke the time may vary