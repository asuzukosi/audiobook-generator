# Following pip packages need to be installed:
# !pip install git+https://github.com/huggingface/transformers sentencepiece datasets

from transformers import set_seed, SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset
import numpy as np
import torch
import soundfile as sf
from datasets import load_dataset
import nltk
from pydub import AudioSegment
import re
import inflect
import os

set_seed(555)

device = "cuda:0" if torch.cuda.is_available() else "cpu"
print("Using device : " + device)

def speed_change(sound, speed=1.0):
    # Manually override the frame_rate. This tells the computer how many
    # samples to play per second
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * speed)
    })
    # convert the sound with altered frame rate to a standard frame rate
    # so that regular playback programs will work right. They often only
    # know how to play audio at standard frame rate (like 44.1k)
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

def SetupModelMicrosoft(model="microsoft_speecht5"):
    processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
    model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts").to(device)
    vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan").to(device)
    # load xvector containing speaker's voice characteristics from a dataset
    embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
    speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0).to(device)
    return (processor, model, vocoder, embeddings_dataset, speaker_embeddings)

processor, model, vocoder, embeddings_dataset, speaker_embeddings = SetupModelMicrosoft()



def cleanText(text):
    # get all the numbers in the text sequence
    nums = re.findall(r'\d+', text) 
    # dictionary used to map numberical values to their word formats
    replacementMap = {}
    
    # go through all the numbers convert the number to ints 
    # word format, then add it to them to replacement map
    for n in nums:
        p = inflect.engine()
        value = p.number_to_words(int(n))
        replacementMap[n] = value
    
    # go through all the values in the replacement map, 
    # replace all numberical values with their word counterparts
    for k, v in replacementMap.items():
        text = text.replace(k, v)
    # return formated text
    return text


def generateInputSequences(text, step_size=500):
    """
    Generate the input sequences that will be passed into the model for 
    inference
    text: the text to be split 
    step_size: the minimum size of each split
    """
    # get the length of the text
    text += " "
    padding = " " * 5
    text_size = len(text)
    # get the number of times the text should be split
    times = int(len(text)// step_size)
    
    # the starting point for each split, for the first split the starting point is 0
    start = 0
    
    # list containing the generated inputs
    inputs = []
    
    for _ in range(0, times):
        # set the step to the minimum step size
        step = step_size
        
        # while the last value after the step is smaller than the text size and 
        # the second to the last value is not equal to an empty space, we will add one 
        # to the step size, this to ensure that inputs don't get cut mid word
        while (start+step) < text_size and text[start+step-1] != " ":
            step += 1
        
        # we will set the data to be the space between the start and sum of the start and step
        data = padding + text[start:start+step]
                
        # add to input
        inputs.append(data)
        # update the starting point
        start += step
    
    # if the starting point is still less that the text size then we will append 
    # the remaining texts to form the last element in the inputs
    if start < text_size:
        inputs.append(text[start:])
    
    return inputs

def processDataAndReturnTensor(data):
    # generate endoding for the data
    data = data.strip()
    data += "."
    # remove  hyphens to make speaker more fluent for unfamiliar words
    data = data.replace("'", "") 
    tensor = processor(text=data, return_tensors="pt")["input_ids"].to(device)
    return tensor
    
    
def speechGeneratorMicrosoft(text, fileName, pageMap):
    # create temporary file path
    filePath = f"{fileName}.mp3"
    if os.path.exists(filePath):
        pageMap[fileName] = True
        print(f"Skipping {fileName}")
        return
    # generate list of input sequences from the text
    print("genrating input sequence")
    text = cleanText(text)
    inputs = generateInputSequences(text, 450)
    
    # create list to store concatenated output from individual inputs
    output = torch.tensor([]).to(device)
    # convert all the text data inputs to tensors using the processor and move them to the device
    inputs = [processDataAndReturnTensor(data) for data in inputs]
    print("Done generating input sequences")
    num_inputs = len(inputs)
    
    print(f"Instance {fileName} has {num_inputs} inputs")
    for id, data in enumerate(inputs):
        # pass input sequence to processor
        print(f"Starting [{id}/{num_inputs}, {fileName}]")
        speech = model.generate_speech(data, speaker_embeddings, vocoder=vocoder)
        output = torch.cat([output, speech], axis=0)
        print(f"Finish [{id}/{num_inputs}, {fileName}]")
    
    output = output.cpu().numpy()
    pageMap[fileName] = True
    print("Done with ", fileName)
    sf.write(filePath, output, samplerate=16000)
    del output
    return
    
    # audio = AudioSegment.from_mp3(filePath)
    # print("Generating audio segmentation")
    # print({
    #     'duration' : audio.duration_seconds,
    #     'sample_rate' : audio.frame_rate,
    #     'channels' : audio.channels,
    #     'sample_width' : audio.sample_width,
    #     'frame_count' : audio.frame_count(),
    #     'frame_rate' : audio.frame_rate,
    #     'frame_width' : audio.frame_width,
    #     })
    # audio = speed_change(audio, 0.95)
    # os.remove(filePath)
    # return audio
