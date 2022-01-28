from cProfile import label
from obspy import read
from obspy.core import Stream
from numpy import abs, fft, argsort, sqrt, mean
import matplotlib.pyplot as plt
import click

def spectrum(trace):
    time_step = 1.0/trace.stats.sampling_rate
    ps = abs(fft.fft(trace.data))**2
    ps = sqrt(ps)
    freqs = fft.fftfreq(trace.data.size, time_step)
    idx = argsort(freqs)
    fresult = freqs[idx]
    psresult = ps[idx]
    l = int(len(fresult)/2)
    return fresult[l:], psresult[l:]

def getLowFreqIndex(freq, lowF):
    for i, f in enumerate(freq):
        if f > lowF:
            return i

def getHighFreqIndex(freq, highF):
    i = len(freq)-1
    while(i > 0):
        if freq[i] < highF:
            return i
        i -= 1


def getMeanSpectrum(freq, spec, lowF, highF):
    bottom = getLowFreqIndex(freq, lowF)
    up = getHighFreqIndex(freq, highF)
    selectedSpec = spec[bottom:up]
    return mean(selectedSpec)

def readComp(filepath,comp):
    st = read(filepath)
    return st.select(component=comp)[0]

#PS-BRT-GEOBIT325-PS001-12022022_Z.mseed
def getDateFrom(tr):
    utcTime = tr.stats.starttime
    localTime = utcTime + 25200
    return localTime.strftime("%d/%m/%y")

def getSensorFrom(filename):
    # filename = "PS-BRT-GEOBIT325-PS001-12022022_Z.mseed"
    return filename.split('-')[2]

def addcalculation(filename, comp="Z"):
    tr = readComp(filename,comp)
    freq, spec = spectrum(tr)
    meanSpec = getMeanSpectrum(freq, spec, 1, 5)
    sensor = getSensorFrom(filename)
    recd = getDateFrom(tr)
    dataLine = sensor+' '+comp+' '+recd+' '+str(meanSpec)
    print(dataLine)
    # Append-adds at last
    file1 = open("FILE-KALIBRASI.txt", "a")  # append mode
    file1.write(dataLine+" \n")
    file1.close()

def readCalFile(filepath, comp="Z"):
    f = open(filepath, "r")
    data={}
    for line in f:
        line = line.split(' ')
        calibrationValue = float(line[3])
        sensor = line[0]
        key = line[2]
        component = line[1]
        if comp != component:
            continue
        if key in data:
            data[key][0].append(sensor)
            data[key][1].append(calibrationValue)
        else:
            data[key] = [[sensor], [calibrationValue]]
    f.close()
    return data

def reformat(data):
    newData = {}
    for key in data:
        for i, sensor in enumerate(data[key][0]):
            value = data[key][1][i]
            if sensor in newData:
                newData[sensor][0].append(key)
                newData[sensor][1].append(value)
            else:
                newData[sensor] = [[key],[value]]
    return newData

def normalize(data):
    for date in data:
        refIndex = 0
        for i, sensor in enumerate(data[date][0]):
            if sensor == 'GEOBIT1':
                refIndex = i
        referenceValue = data[date][1][refIndex]
        for key in data:
            for i in range(len(data[key][1])):
                data[key][1][i] /= referenceValue
        return data

def generateCalData(filename,comp="Z"):
    data = readCalFile(filename)
    data = normalize(data)
    data = reformat(data)
    return data

def plotData(dataZ, dataN, dataE):
    fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)
    fig.set_size_inches(8.2, 11)
    fig.suptitle("Grafik Kalibrasi Harian Survei Seismik Pasif Area Piraiba dan Tanjung Barat")
    # ax1.plot(x, y)
    for key in dataZ:
        ax1.plot(dataZ[key][0],dataZ[key][1], '-o', label=key)
    for key in dataN:
        ax2.plot(dataN[key][0],dataZ[key][1], '-o', label=key)
    for key in dataE:
        ax3.plot(dataE[key][0],dataZ[key][1], '-o', label=key)
    # ax1.legend()
    ax1.legend(bbox_to_anchor=(1, 1.2),ncol = len(ax1.lines))
    ax1.set_ylabel('Komponen Z')
    ax2.set_ylabel('Komponen N')
    ax3.set_ylabel('Komponen E')
    ax1.yaxis.tick_right()
    ax2.yaxis.tick_right()
    ax3.yaxis.tick_right()
    plt.xlabel("Tanggal")
    plt.xticks(rotation=90)
    plt.savefig("GrafikKalibrasiHarian.png")

@click.group()
def main():
    pass

@click.command()
@click.argument('filename', type=click.Path(exists=True),nargs=-1)
def add(filename):
    for item in filename:
        addcalculation(item,'Z')
        addcalculation(item,'N')
        addcalculation(item,'E')


@click.command()
@click.argument('filename', type=click.Path(exists=True))
def plot(filename):
    print("Plot daily calibration data")
    dataZ = generateCalData(filename, "Z")
    dataN = generateCalData(filename, "N")
    dataE = generateCalData(filename, "E")
    plotData(dataZ, dataN, dataE)

main.add_command(add)
main.add_command(plot)

if __name__ == '__main__':
    main()