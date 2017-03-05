from flask import Flask, redirect, render_template, request, session, url_for

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/result", methods=["POST"])
def result():
    # Imports the Google Cloud client library
    from google.cloud import language
    import numpy, re
    from scipy import stats

    # Instantiates a client
    language_client = language.Client()

    # The text to analyze
    para = request.form["text"]
    thresholdFactor = int(request.form["thresholdFactor"])
    text = re.split(r'[.!?]+', para)
    print(text)

    pair_message = []

    for data in text:
        data = data.strip()
        document = language_client.document_from_text(data)
        # Detects the sentiment of the text
        sentiment = document.analyze_sentiment().sentiment
        pair_message.append([data, sentiment.magnitude])

    print("Length of text", len(pair_message))

    mean_mag = numpy.mean([x[1] for x in pair_message])
    median_mag = numpy.median([x[1] for x in pair_message])

    print
    processed_text = ""
    count = 0
    threshold = min(mean_mag, median_mag)
    for sentence in pair_message:
        if sentence[1] >= threshold * ((thresholdFactor - 0.5)/ 2):
            count += 1
            location = para.index(sentence[0])
            processed_text += para[location:location + len(sentence[0]) + 1] + " "
    return render_template("success.html", display = processed_text)
