if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Simple Audio file combiner using MoviePy library in Python")
    parser.add_argument("-c", "--clips", nargs="+",
                        help="List of audio clip paths")
    parser.add_argument("-o", "--output", help="The output audio file, extension must be included (such as mp3, etc.)")
    args = parser.parse_args()
    concatenate_audio_moviepy(args.clips, args.output)
    
    
'''
Sample Usage 

-----------
$ python concatenate_audio_moviepy.py -c zoo.mp3 directed-by-robert.mp3 -o output_moviepy.mp3
MoviePy - Writing audio in output_moviepy.mp3
MoviePy - Done.
'''