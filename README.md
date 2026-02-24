# imgpdf2csv

Idea: Take a PDF that is mostly constructed of images, read those images, and
put their text in a csv file.

```
# create the container
`distrobox create --name pdf-tool --image fedora:latest`
# enter the container
`distrobox enter pdf-tool`

# inside the container:

# install dependencies
sudo dnf install tesseract tesseract-langpack-eng poppler-utils python5-pip -y
# install OpenGL
sudo dnf install mesa-libGL -y

# use python 3.12 (so that we can use the latest img2table)
sudo dnf install python3.12 python3.12-devel -y
# explicitly use python 3.12
python3.12 -m venv venv
source venv/bin/activate

# upgrade pip (if necessary)
pip install --upgrade pip
# install necessary libraries
pip install --no-cache-dir img2table pdf2image pandas pytesseract more-itertools
```

# imgpdf2txt

```
sudo dnf install tesseract tesseract-langpack-eng poppler-utils -y
pip install pytesseract pdf2image

python imgpdf2txt.py docs/fire.pdf 7 > outputs/pages-7-onwards.out
# generates cleaned_pages-7-onwards.out
python trim-cruft.py outputs/pages-7-onwards.out
mv cleaned_pages-7-onwards.out outputs/.
python stitch-lines.py outputs/cleaned_pages-7-onwards.out
```
