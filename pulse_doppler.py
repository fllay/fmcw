#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Pulse Doppler Processing
# Author: Shane Flandermeyer
# Description: Example of range and doppler processing
# GNU Radio version: 3.10.7.0

from packaging.version import Version as StrictVersion
from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import Qt
from gnuradio import plasma
import sip
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation



class pulse_doppler(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Pulse Doppler Processing", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Pulse Doppler Processing")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "pulse_doppler")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 20e6
        self.n_pulse_cpi = n_pulse_cpi = 512
        self.center_freq = center_freq = 2.45e9
        self.bandwidth = bandwidth = 0.75*samp_rate

        ##################################################
        # Blocks
        ##################################################

        self.plasma_waveform_controller_0 = plasma.waveform_controller(10000, samp_rate)
        self.plasma_waveform_controller_0.init_meta_dict('radar:prf', 'core:sample_rate')
        self.plasma_usrp_radar_0 = plasma.usrp_radar('num_send_frames=512,num_recv_frames=512')
        self.plasma_usrp_radar_0.set_metadata_keys('core:frequency', 'radar:prf', 'core:sample_start')
        self.plasma_usrp_radar_0.set_samp_rate(samp_rate)
        self.plasma_usrp_radar_0.set_tx_gain(70)
        self.plasma_usrp_radar_0.set_rx_gain(60)
        self.plasma_usrp_radar_0.set_tx_freq(center_freq)
        self.plasma_usrp_radar_0.set_rx_freq(center_freq)
        self.plasma_usrp_radar_0.set_start_time(0.2)
        self.plasma_usrp_radar_0.set_tx_thread_priority(1.0)
        self.plasma_usrp_radar_0.set_rx_thread_priority(1.0)
        self.plasma_usrp_radar_0.read_calibration_file("/home/pi/delay.json")
        self.plasma_range_doppler_sink_0 = plasma.range_doppler_sink(samp_rate, n_pulse_cpi, center_freq)
        self.plasma_range_doppler_sink_0.set_metadata_keys('core:sample_rate', 'n_matrix_col', 'core:frequency', 'dynamic_range', 'radar:prf', 'radar:duration', 'detection_indices')
        self.plasma_range_doppler_sink_0.set_dynamic_range(80)
        self.plasma_range_doppler_sink_0.set_msg_queue_depth(1)
        self._plasma_range_doppler_sink_0_win = sip.wrapinstance(self.plasma_range_doppler_sink_0.pyqwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._plasma_range_doppler_sink_0_win)
        self.plasma_pulse_to_cpi_0 = plasma.pulse_to_cpi(n_pulse_cpi)
        self.plasma_pulse_to_cpi_0.init_meta_dict('radar:n_pulse_cpi')
        self.plasma_match_filt_0 = plasma.match_filt(n_pulse_cpi)
        self.plasma_match_filt_0.set_metadata_keys('n_pulse_cpi')
        self.plasma_match_filt_0.set_msg_queue_depth(1)
        self.plasma_match_filt_0.set_backend(plasma.Device.DEFAULT)
        self.plasma_lfm_source_0 = plasma.lfm_source(0.8*samp_rate, -bandwidth/2, 20e-6, samp_rate)
        self.plasma_lfm_source_0.init_meta_dict('radar:bandwidth', 'radar:start_freq', 'radar:duration', 'core:sample_rate', 'core:label')
        self.plasma_doppler_processing_0 = plasma.doppler_processing(n_pulse_cpi, n_pulse_cpi)
        self.plasma_doppler_processing_0.set_msg_queue_depth(1)
        self.plasma_doppler_processing_0.set_backend(plasma.Device.DEFAULT)
        self.plasma_doppler_processing_0.set_metadata_keys('n_pulse_cpi', 'doppler_fft_size')
        self.plasma_cfar2D_0 = plasma.cfar2D((2,2), (3,3), 1e-6,n_pulse_cpi)
        self.plasma_cfar2D_0.set_msg_queue_depth(1)
        self.plasma_cfar2D_0.set_backend(plasma.Device.DEFAULT)
        self.plasma_cfar2D_0.set_metadata_keys('detection_indices', 'n_detections', 'n_pulse_cpi')


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.plasma_cfar2D_0, 'out'), (self.plasma_range_doppler_sink_0, 'in'))
        self.msg_connect((self.plasma_doppler_processing_0, 'out'), (self.plasma_cfar2D_0, 'in'))
        self.msg_connect((self.plasma_lfm_source_0, 'out'), (self.plasma_match_filt_0, 'tx'))
        self.msg_connect((self.plasma_lfm_source_0, 'out'), (self.plasma_waveform_controller_0, 'in'))
        self.msg_connect((self.plasma_match_filt_0, 'out'), (self.plasma_doppler_processing_0, 'in'))
        self.msg_connect((self.plasma_pulse_to_cpi_0, 'out'), (self.plasma_match_filt_0, 'rx'))
        self.msg_connect((self.plasma_usrp_radar_0, 'out'), (self.plasma_pulse_to_cpi_0, 'in'))
        self.msg_connect((self.plasma_waveform_controller_0, 'out'), (self.plasma_usrp_radar_0, 'in'))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "pulse_doppler")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_bandwidth(0.75*self.samp_rate)

    def get_n_pulse_cpi(self):
        return self.n_pulse_cpi

    def set_n_pulse_cpi(self, n_pulse_cpi):
        self.n_pulse_cpi = n_pulse_cpi

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq

    def get_bandwidth(self):
        return self.bandwidth

    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth




def main(top_block_cls=pulse_doppler, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
