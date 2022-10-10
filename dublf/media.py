import os
import re

RE_DIGITS = re.compile('(\\d+)')

def getSequence(path):
    """Returns the file sequence found from a single file or the containing folder"""

    # If path is a folder, try with the first file found
    if os.path.isdir(path):
        files = os.listdir(path)
        if len(files) > 0:
            path = os.path.join(path, files[0])
        else:
            return ()
    # Wrong path, return
    elif not os.path.isfile(path):
        return()

    # The folder and all its files
    containingDir = os.path.dirname(path)
    allFiles = os.listdir(containingDir)
    fileTuple = os.path.splitext( os.path.basename(path) )
    fileName = fileTuple[0]
    fileExt = fileTuple[1]

    # The list of frames
    frames = [path]

    # find the digits blocks to check if we've got a sequence
    matches = RE_DIGITS.findall(fileName)
    for digits in matches:
        # List oll files matching the pattern
        blocks = fileName.split( digits )
        left = blocks[0]
        right = blocks[1]
        pattern = left + '(\\d+)' + right
        # Number of digits
        numDigits = len(digits)
        # list potential files in the sequence
        for file in allFiles:
            test = re.findall(pattern, file)
            if len(test) == 0:
                continue
            testDigits = test[0]
            # That's the same number, can't be the digits
            if testDigits == digits:
                continue
            # Not the same number of digits
            if len(testDigits) != numDigits:
                continue
            # This must be it
            frames.append(
                os.path.join(containingDir, file)
            )
        # if we've found frames, we've got a sequence
        if len(frames) > 1:
            return frames

    return frames

if __name__ == "__main__":
    p = "D:/RxLab/Gestion/CLIENTS-COMMANDES/MadLab/exemples/Exemple d'un dossier export contenant une sequence d'image/687/ANIM"
    print( getSequence(p) )