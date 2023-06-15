import pdfplumber
import PyPDF2
from aiReader import speechGeneratorMicrosoft
from pydub import AudioSegment
from math import ceil
import argparse
import threading


# This is the function where each page would be handled to generate audio
def handlePage(page, pageChecker, text):
    speechGeneratorMicrosoft(text, str(page))
    pageChecker[page] = True
    print("Page :" + str(page) + "is Done!")
  
# Add background music to audio sequence
def addBackground(audio, background):
    times = int(ceil(audio.frame_count() // background.frame_count()))
    full_audio = background
    for _ in range(1, times):
        full_audio += background
        
    background = full_audio
    background -= 10
    audio += 10
    combined = audio.overlay(background)
    return combined

def buildFullAudioFromPDF(file, output):
	#Creating a PDF File Object
	pdfFileObj = open(file, 'rb')

	# creating a pdf reader object
	pdfReader = PyPDF2.PdfFileReader(pdfFileObj)

	#Get the number of pages
	pages = pdfReader.numPages
	# pages have been visited
	pageMap = {}

	# set all the values on the page mapper to false by default. 
	# This means that they have not been parsed
	for i in range(0, pages):
		pageMap[i] = False
 
	audio_sequences = []
	with pdfplumber.open(file) as pdf:
		for i in range(0, pages):
			page = pdf.pages[i]
			text = page.extract_text()
			print("Starting page: ", i+1)
			# audio = speechGeneratorMicrosoft(text, str(i))
			thread = threading.Thread(target=speechGeneratorMicrosoft, kwargs={"text": text, "fileName": str(i)})
			thread.start()
			# audio_sequences.append(audio)
			# print("Done with page ", i+1)

	# print("Stringing up sequences together")
	# final_sequence = audio_sequences[0]
	# for i in range(1, len(audio_sequences)):
	# 	final_sequence += audio_sequences[i]

	# print("Generating final mp3 with background")
	# background = AudioSegment.from_mp3("background/beach_waves.mp3")
	# final = addBackground(final_sequence, background)
	# final.export(output)

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI audio book generator")
    parser.add_argument("-i", "--input",
                        help="Input pdf file", required=True)
    parser.add_argument("-o", "--output", help="The output mp3 file where the generated audio will be stored", required=True)
    args = parser.parse_args()
    buildFullAudioFromPDF(args.input, args.output)