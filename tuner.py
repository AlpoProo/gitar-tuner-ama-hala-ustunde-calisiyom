import sys
import numpy as np
import pyaudio
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QComboBox
from PyQt5.QtGui import QFont

RATE = 44100
CHUNK = 4096
AVERAGE_COUNT = 5

standard_tuning = {
    "E2": 82.4,
    "A2": 110.0,
    "D3": 146.8,
    "G3": 196.0,
    "B3": 246.9,
    "E4": 329.6
}

drop_d_tuning = {
    "D2": 73.42,
    "A2": 110.0,
    "D3": 146.8,
    "G3": 196.0,
    "B3": 246.9,
    "E4": 329.6
}

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

recent_frequencies = []

class GitarTuner(QWidget):
    def __init__(self):
        super().__init__()
        self.current_tuning = standard_tuning  
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.tuning_combobox = QComboBox(self)
        self.tuning_combobox.addItem("Standard Tuning", standard_tuning)
        self.tuning_combobox.addItem("Drop D Tuning", drop_d_tuning)
        self.tuning_combobox.currentIndexChanged.connect(self.change_tuning)
        layout.addWidget(self.tuning_combobox)

        self.result_label = QLabel('Teli çal ve sonucu bekleyin', self)
        self.result_label.setFont(QFont('Arial', 24))
        layout.addWidget(self.result_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

        self.setGeometry(200, 200, 400, 200)
        self.setWindowTitle('Gitar Tuner')
        self.show()

        self.detect_note()

    def change_tuning(self):
        self.current_tuning = self.tuning_combobox.currentData()

    def detect_note(self):
        data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
        windowed_data = data * np.hanning(CHUNK)
        fft = np.fft.fft(windowed_data)
        freq = np.fft.fftfreq(CHUNK, 1/RATE)
        magnitude = np.abs(fft)
        peak_frequency = abs(freq[np.argmax(magnitude)])

        recent_frequencies.append(peak_frequency)
        if len(recent_frequencies) > AVERAGE_COUNT:
            recent_frequencies.pop(0)
        avg_frequency = np.mean(recent_frequencies)

        closest_string = min(self.current_tuning.keys(), key=lambda note: abs(self.current_tuning[note] - avg_frequency))
        closest_freq = self.current_tuning[closest_string]

        difference = avg_frequency - closest_freq
        if abs(difference) <= 0.5:
            self.result_label.setText(f"{closest_string} (Tamam)")
            self.progress_bar.setValue(100)
        elif difference < 0:
            self.result_label.setText(f"{closest_string} (Düşük)")
            self.progress_bar.setValue(int(100 * (1 + difference / closest_freq)))
        else:
            self.result_label.setText(f"{closest_string} (Yüksek)")
            self.progress_bar.setValue(int(100 * (1 - difference / closest_freq)))

        self.progress_bar.setStyleSheet(self.get_bar_color(difference))

        QApplication.processEvents()
        self.detect_note()

    def get_bar_color(self, difference):
        if abs(difference) <= 0.5:
            return "QProgressBar::chunk { background-color: green; }"
        elif difference < 0:
            return "QProgressBar::chunk { background-color: blue; }"
        else:
            return "QProgressBar::chunk { background-color: red; }"

if __name__ == '__main__':
    app = QApplication(sys.argv)
    tuner = GitarTuner()
    sys.exit(app.exec_())
