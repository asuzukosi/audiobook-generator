import pdfplumber
import PyPDF2
from aiReader import speechGeneratorMicrosoft, speed_change
from pydub import AudioSegment
from math import ceil
import argparse
import threading
import numpy as np
import soundfile as sf


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

def ensureComplete(pageMap, lim):
    while True:
        should_break = True
        for i in range(0, lim):
            if not pageMap[i]:
                should_break = False
        if should_break:
            return

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
		pageMap[i] = None
 
	audio_sequences = np.array([])
	step_size = 25
	print("Number of pages are: " + str(pages))
 
	with pdfplumber.open(file) as pdf:
		batch =  0
		for i in range(0, pages, step_size):
			batch += 1
			print(f"##### Starting batch {batch} ######")
			lim = min(i+step_size, pages) # the limit for this batch
			for j in range(i, lim):
				page = pdf.pages[j]
				text = page.extract_text()
				print("Starting page: ", j+1)
				# audio = speechGeneratorMicrosoft(text, str(i))
				thread = threading.Thread(target=speechGeneratorMicrosoft, kwargs={"text": text, 
                                                                       			   "fileName": j, 
                                                                             	   "pageMap": pageMap})
				thread.start()

			ensureComplete(pageMap, lim)
			print(f"#### Finished batch {batch}#####")

			# audio_sequences.append(audio)
			# print("Done with page ", i+1)
   
	print("Stringing up sequences together")
	for k, v in pageMap.items():
		audio_sequences = np.concatenate(audio_sequences, k, axis=1)
  
	sf.write(output, audio_sequences, samplerate=16000)
	final_sequence = AudioSegment.from_mp3(output)
	print("Geneating audio sequence")
	print({
        'duration' : final_sequence.duration_seconds,
        'sample_rate' : final_sequence.frame_rate,
        'channels' : final_sequence.channels,
        'sample_width' : final_sequence.sample_width,
        'frame_count' : final_sequence.frame_count(),
        'frame_rate' : final_sequence.frame_rate,
        'frame_width' : final_sequence.frame_width,
        })
	final_sequence = speed_change(final_sequence, 0.95)

	print("Generating final mp3 with background")
	background = AudioSegment.from_mp3("background/beach_waves.mp3")
	final = addBackground(final_sequence, background)
	final.export(output)

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI audio book generator")
    parser.add_argument("-i", "--input",
                        help="Input pdf file", required=True)
    parser.add_argument("-o", "--output", help="The output mp3 file where the generated audio will be stored", required=True)
    args = parser.parse_args()
    buildFullAudioFromPDF(args.input, args.output)