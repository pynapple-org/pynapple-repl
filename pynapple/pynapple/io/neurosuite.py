"""
> :warning: **DEPRECATED**: This will be removed in version 1.0.0. Check [nwbmatic](https://github.com/pynapple-org/nwbmatic) or [neuroconv](https://github.com/catalystneuro/neuroconv) instead.

Class and functions for loading data processed with the Neurosuite (Klusters, Neuroscope, NDmanager)

@author: Guillaume Viejo
"""

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .. import core as nap
from .loader import BaseLoader


class NeuroSuite(BaseLoader):
    """
    Loader for kluster data
    """

    def __init__(self, path):
        """
        Instantiate the data class from a neurosuite folder.

        Parameters
        ----------
        path : str
            The path to the data.
        """
        path = Path(path)
        self.basename = path.name
        self.time_support = None

        super().__init__(path)

        self.load_nwb_spikes()

    def load_nwb_spikes(self):
        """
        Read the NWB spikes to extract the spike times.

        Parameters
        ----------
        path : str
            The path to the data

        Returns
        -------
        TYPE
            Description
        """
        pynwb = importlib.import_module("pynwb")
        io = pynwb.NWBHDF5IO(self.nwbfilepath, "r")
        nwbfile = io.read()

        if nwbfile.units is None:
            io.close()
            return False
        else:
            units = nwbfile.units.to_dataframe()
            spikes = {
                n: nap.Ts(t=units.loc[n, "spike_times"], time_units="s")
                for n in units.index
            }

            self.spikes = nap.TsGroup(
                spikes,
                time_support=self.time_support,
                time_units="s",
                group=units["group"],
            )

            if ~np.all(units["location"] == ""):
                self.spikes.set_info(location=units["location"])

            io.close()
            return True

    def load_lfp(
        self,
        filename=None,
        channel=None,
        extension=".eeg",
        frequency=1250.0,
        precision="int16",
        bytes_size=2,
    ):
        """
        Load the LFP.

        Parameters
        ----------
        filename : str, optional
            The filename of the lfp file.
            It can be useful it multiple dat files are present in the data directory
        channel : int or list of int, optional
            The channel(s) to load. If None return a memory map of the dat file to avoid memory error
        extension : str, optional
            The file extenstion (.eeg, .dat, .lfp). Make sure the frequency match
        frequency : float, optional
            Default 1250 Hz for the eeg file
        precision : str, optional
            The precision of the binary file
        bytes_size : int, optional
            Bytes size of the lfp file

        Raises
        ------
        RuntimeError
            If can't find the lfp/eeg/dat file

        Returns
        -------
        Tsd or TsdFrame
            The lfp in a time series format
        """
        if filename is not None:
            filepath = self.path / filename
        else:
            filepath = Path(filename)
            eegfile = list(filepath.glob(f"*{extension}"))

            if not len(eegfile):
                raise RuntimeError(
                    "Path {} contains no {} files;".format(self.path, extension)
                )

            filepath = eegfile[0]

        self.load_neurosuite_xml(self.path)

        n_channels = int(self.nChannels)

        f = open(filepath, "rb")
        startoffile = f.seek(0, 0)
        endoffile = f.seek(0, 2)
        bytes_size = 2
        n_samples = int((endoffile - startoffile) / n_channels / bytes_size)
        duration = n_samples / frequency
        f.close()
        fp = np.memmap(filepath, np.int16, "r", shape=(n_samples, n_channels))
        timestep = np.arange(0, n_samples) / frequency

        time_support = nap.IntervalSet(start=0, end=duration, time_units="s")

        if channel is None:
            return nap.TsdFrame(
                t=timestep, d=fp, time_units="s", time_support=time_support
            )
        elif type(channel) is int:
            return nap.Tsd(
                t=timestep, d=fp[:, channel], time_units="s", time_support=time_support
            )
        elif type(channel) is list:
            return nap.TsdFrame(
                t=timestep,
                d=fp[:, channel],
                time_units="s",
                time_support=time_support,
                columns=channel,
            )

    def read_neuroscope_intervals(self, name=None, path2file=None):
        """
        This function reads .evt files in which odd raws indicate the beginning
        of the time series and the even raws are the ends.
        If the file is present in the nwb, provide the just the name. If the file
        is not present in the nwb, it loads the events from the nwb directory.
        If just the path is provided but not the name, it takes the name from the file.

        Parameters
        ----------
        name: str
            name of the epoch in the nwb file, e.g. "rem" or desired name save
            the data in the nwb.

        path2file: str
            Path of the file you want to load.

        Returns
        -------
        IntervalSet
            Contains two columns corresponding to the start and end of the intervals.

        """
        # if name:
        #     isets = self.load_nwb_intervals(name)
        #     if isinstance(isets, nap.IntervalSet):
        #         return isets

        if name is not None and path2file is None:
            path2file = self.path / (self.basename + "." + name + ".evt")
        if path2file is not None:  # TODO maybe useless conditional?
            try:
                # df = pd.read_csv(path2file, delimiter=' ', usecols = [0], header = None)
                tmp = np.genfromtxt(path2file)[:, 0]
                df = tmp.reshape(len(tmp) // 2, 2)
            except ValueError:
                print("specify a valid name")
            isets = nap.IntervalSet(df[:, 0], df[:, 1], time_units="ms")
            if name is None:
                name = path2file.split(".")[-2]
                print("*** saving file in the nwb as", name)
            # self.save_nwb_intervals(isets, name)
        else:
            raise ValueError("specify a valid path")
        return isets

    def write_neuroscope_intervals(self, extension, isets, name):
        """Write events to load with neuroscope (e.g. ripples start and ends)

        Parameters
        ----------
        extension : str
            The extension of the file (e.g. basename.evt.py.rip)
        isets : IntervalSet
            The IntervalSet to write
        name : str
            The name of the events (e.g. Ripples)
        """
        start = isets.as_units("ms")["start"].values
        ends = isets.as_units("ms")["end"].values

        datatowrite = np.vstack((start, ends)).T.flatten()

        n = len(isets)

        texttowrite = np.vstack(
            (
                (np.repeat(np.array([name + " start"]), n)),
                (np.repeat(np.array([name + " end"]), n)),
            )
        ).T.flatten()

        evt_file = self.path / (self.basename + extension)

        f = open(evt_file, "w")
        for t, n in zip(datatowrite, texttowrite):
            f.writelines("{:1.6f}".format(t) + "\t" + n + "\n")
        f.close()

        return

    def load_mean_waveforms(self, epoch=None, waveform_window=None, spike_count=1000):
        """
        Load the mean waveforms from a dat file.

        Parameters
        ----------
        epoch : IntervalSet
            default = None
            Restrict spikes to an epoch.
        waveform_window : IntervalSet
            default interval nap.IntervalSet(start = -0.0005, end = 0.001, time_units = 'ms')
            Limit waveform extraction before and after spike time
        spike_count : int
            default = 1000
            Number of spikes used per neuron for the calculation of waveforms

        Returns
        -------
        dictionary
            the waveforms for all neurons
        pandas.Series
            the channel with the maximum waveform for each neuron

        """
        if not isinstance(waveform_window, nap.IntervalSet):
            waveform_window = nap.IntervalSet(start=-0.5, end=1, time_units="ms")

        spikes = self.spikes
        if not self.path.exists():  # check if path exists
            print("The path " + self.path + " doesn't exist; Exiting ...")
            sys.exit()

        # Load XML INFO
        self.load_neurosuite_xml(self.path)
        n_channels = self.nChannels
        fs = self.fs_dat
        group_to_channel = self.group_to_channel
        group = spikes.get_info("group")

        # Check if there is an epoch, restrict spike times to epoch
        if epoch is not None:
            if type(epoch) is not nap.IntervalSet:
                print("Epoch must be an IntervalSet")
                sys.exit()
            else:
                print("Restricting spikes to epoch")
                spikes = spikes.restrict(epoch)
                epstart = int(epoch.as_units("s")["start"].values[0] * fs)
                epend = int(epoch.as_units("s")["end"].values[0] * fs)

        # Find dat file
        # files = os.listdir(self.path)
        #  dat_files = np.sort([f for f in files if "dat" in f and f[0] != "."])

        # Need n_samples collected in the entire recording from dat file to load
        # file = self.path / dat_files[0]
        file = next(self.path.glob("^[^.][^.]*.dat"))
        f = open(
            file, "rb"
        )  # open file to get number of samples collected in the entire recording
        startoffile = f.seek(0, 0)
        endoffile = f.seek(0, 2)
        bytes_size = 2
        n_samples = int((endoffile - startoffile) / n_channels / bytes_size)
        f.close()
        # map to memory all samples for all channels, channels are numbered according to neuroscope number
        fp = np.memmap(file, np.int16, "r", shape=(n_samples, n_channels))

        # convert spike times to spikes in sample number
        sample_spikes = {
            neuron: (spikes[neuron].as_units("s").index.values * fs).astype("int")
            for neuron in spikes
        }

        # prep for waveforms
        overlap = int(
            waveform_window.tot_length(time_units="s")
        )  # one spike's worth of overlap between windows
        waveform_window = abs(np.array(waveform_window.as_units("s"))[0] * fs).astype(
            int
        )  # convert time to sample number
        neuron_waveforms = {
            n: np.zeros([np.sum(waveform_window), len(group_to_channel[group[n]])])
            for n in sample_spikes
        }

        # divide dat file into batches that slightly overlap for faster loading
        batch_size = 3000000
        windows = np.arange(0, int(endoffile / n_channels / bytes_size), batch_size)
        if epoch is not None:
            print("Restricting dat file to epoch")
            windows = windows[(windows >= epstart) & (windows <= epend)]
        batches = []
        for (
            i
        ) in windows:  # make overlapping batches from the beginning to end of recording
            if i == windows[-1]:  # the last batch cannot overlap with the next one
                batches.append([i, n_samples])
            else:
                batches.append([i, i + batch_size + overlap])
        batches = [np.int32(batch) for batch in batches]

        sample_counted_spikes = {}
        for index, neuron in enumerate(sample_spikes):
            if len(sample_spikes[neuron]) >= spike_count:
                sample_counted_spikes[neuron] = np.array(
                    np.random.choice(list(sample_spikes[neuron]), spike_count)
                )
            elif len(sample_spikes[neuron]) < spike_count:
                print(
                    "Not enough spikes in neuron " + str(index) + "... using all spikes"
                )
                sample_counted_spikes[neuron] = sample_spikes[neuron]

        # Make one array containing all selected spike times of all neurons - will be used to check for spikes before loading dat file
        spike_check = np.array(
            [
                int(spikes_neuron)
                for spikes_neuron in sample_counted_spikes[neuron]
                for neuron in sample_counted_spikes
            ]
        )

        for index, timestep in enumerate(batches):
            print(
                f"Extracting waveforms from dat file: window {index+1} / {len(windows)}",
                end="\r",
            )

            if (
                len(
                    spike_check[
                        (timestep[0] < spike_check) & (timestep[1] > spike_check)
                    ]
                )
                == 0
            ):
                continue  # if there are no spikes for any neurons in this batch, skip and go to the next one

            # Load dat file for timestep
            tmp = pd.DataFrame(
                data=fp[timestep[0] : timestep[1], :],
                columns=np.arange(n_channels),
                index=range(timestep[0], timestep[1]),
            )  # load dat file

            # Check if any spikes are present
            for neuron in sample_counted_spikes:
                neurontmp = sample_counted_spikes[neuron]
                tmp2 = neurontmp[(timestep[0] < neurontmp) & (timestep[1] > neurontmp)]
                if len(neurontmp) == 0:
                    continue  # skip neuron if it has no spikes in this batch
                tmpn = tmp[
                    group_to_channel[group[neuron]]
                ]  # restrict dat file to the channel group of the neuron

                for time in tmp2:  # add each spike waveform to neuron_waveform
                    spikewindow = tmpn.loc[
                        time - waveform_window[0] : time + waveform_window[1] - 1
                    ]  # waveform for this spike time
                    try:
                        neuron_waveforms[neuron] += spikewindow.values
                    except (
                        Exception
                    ):  # ignore if full waveform is not present in this batch
                        pass

        meanwf = {
            n: pd.DataFrame(
                data=np.array(neuron_waveforms[n]) / spike_count,
                columns=np.arange(len(group_to_channel[group[n]])),
                index=np.array(np.arange(-waveform_window[0], waveform_window[1])) / fs,
            )
            for n in sample_counted_spikes
        }

        # find the max channel for each neuron
        maxch = pd.Series(
            data=[meanwf[n][meanwf[n].loc[0].idxmin()].name for n in meanwf],
            index=spikes.keys(),
        )

        return meanwf, maxch
