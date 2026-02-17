# imgpdf2csv

Idea: Take a PDF that is mostly constructed of images, read those images, and
put their text in a csv file.

```
# create the container
`distrobox create --name pdf-tool --image fedora:latest`
# enter the container
`distrobox enter pdf-tool`

# inside the container:
# upgrade pip if necessary
pip install --upgrade pip
# install dependencies
sudo dnf install tesseract tesseract-langpack-eng poppler-utils python5-pip -y
# set up Python container
python3 -m venv venv
source venv/bin/activate
# install necessary libraries
pip install img2table pdf2image pandas pytesseract
```
