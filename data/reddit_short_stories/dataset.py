from dataclasses import dataclass


DATA_PATH = "reddit_short_stories.txt"
URL = "https://github.com/tdude92/reddit-short-stories/blob/main/reddit_short_stories.txt"


"""
Dataset description
Each line of reddit_short_stories.txt is one full short story.
Each short story begins with an "<sos>" token and ends with an "<eos>" token (eg. "<sos> once upon a time, the end <eos>").
Newline characters in a story are replaced with the "<nl>" token (eg. "<sos> line 1 <nl> line 2 <eos>")
"""
@dataclass
class Story:
    _id: int
    text: str

def process_line(line):
    # strip <sos> and <eos> tags and replace <nl> for newlines
    return line.replace("<sos> ", "").replace(" <eos>", "").replace(" <nl> ", "\n")

@dataclass
class RedditShortStoriesDataset:
    def __init__ (self, path=DATA_PATH):
        self.path = path
        self.stories = self.__load()
    
    def __load(self):
        with open(self.path) as f:
            for _id, line in enumerate(f):
                yield Story(_id, process_line(line))
        
    def __iter__(self):
        yield from self.stories



