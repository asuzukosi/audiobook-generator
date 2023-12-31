import pdfplumber
import PyPDF2
from aiReader import speechGeneratorMicrosoft, speed_change
from pydub import AudioSegment
from math import ceil
import argparse
import threading
import numpy as np
import soundfile as sf
import os

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

def buildFullAudioFromPDF(file, output, device):
	#Creating a PDF File Object
	pdfFileObj = open(file, 'rb')
 
	if device == "gpu":
		import torch
		if torch.cuda.is_available() != True:
			raise Exception("GPU not available, running the application will take long")
	
		print("GPU is availabe and ready to go")
	
	print("Using {device} to build")
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
    # specify the step size based on what device is being used
    
	if device == 'cpu':
		step_size = 1
	elif device == 'gpu':
		step_size = 10
  
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
				if device == 'cpu':
					speechGeneratorMicrosoft(text, j, pageMap)
				elif device == 'gpu':
					thread = threading.Thread(target=speechGeneratorMicrosoft, kwargs={"text": text, "fileName": j, "pageMap": pageMap})
					thread.start()
			ensureComplete(pageMap, lim)
			print(f"#### Finished batch {batch}#####")

   
	print("Stringing up sequences together")
	final_sequence = None
	for i in range(0, pages):
		filePath = f"{i}.mp3"
		audio = AudioSegment.from_mp3(filePath)
		# if the final sequence is none i.e this is the first audio, 
  		# then the final sequence should be set to the first audio
		if final_sequence == None:
			final_sequence = audio
		# if final sequence already exists, then add audio to final sequence
		else:
			final_sequence += audio
		# os.remove(filePath)
		
  
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
	# background = AudioSegment.from_mp3("background/beach_waves.mp3")
	# final = addBackground(final_sequence, background)
	final_sequence.export(output)
 
	# delete all intermediate sequences
	print("Deleting intermediate sequences")
	for i in range(pages):
		filePath = f"{i}.mp3"
		os.remove(filePath)
  
	print("Done!")

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI audio book generator")
    parser.add_argument("-i", "--input",
                        help="Input pdf file", required=True)
    parser.add_argument("-o", "--output", help="The output mp3 file where the generated audio will be stored", required=True)
    parser.add_argument("-d", "--device", help="Specify the device to use either cpu or gpu", default="cpu")
    args = parser.parse_args()
    if args.device not in ["cpu", "gpu"]:
        raise Exception("Invalid device specified")
    buildFullAudioFromPDF(args.input, args.output, args.device)