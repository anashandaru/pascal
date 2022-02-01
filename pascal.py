from cProfile import label
from obspy import read
from obspy.core import Stream
from numpy import abs, fft, argsort, sqrt, mean
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
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
    return filename.replace('_','-').split('-')[2]

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

def readCalFile(filepath, comp):
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
            date = datetime.strptime(key,'%d/%m/%y')
            if sensor in newData:
                newData[sensor][0].append(date)
                newData[sensor][1].append(value)
            else:
                newData[sensor] = [[date],[value]]
    return newData

def normalize(data, referenceSensor='GEOBIT1'):
    refDict = {}
    for date in data:
        refIndex = 0
        for i, sensor in enumerate(data[date][0]):
            if sensor == referenceSensor:
                refIndex = i
                referenceValue = data[date][1][refIndex]
                refDict[date] = referenceValue
        
    for date in data:
        for i in range(len(data[date][1])):
            sensor = data[date][0][i]
            ref = refDict[date]
            data[date][1][i] = ref/data[date][1][i]
            print("normalize {} at {} using {}".format(sensor,date,ref))
    return data

def getSorted(x, y):
    return zip(*sorted(zip(x, y)))

def clearNorfile():
    file1 = open("NORMALISASI-FILE-KALIBRASI.txt", "w")  # append mode
    file1.write("")
    file1.close()

def exportToFile(data, comp='Z'):
    for key in data:
        for i, sensor in enumerate(data[key][0]):
            value = data[key][1][i]
            dataLine = sensor+' '+comp+' '+key+' '+str(value)
            file1 = open("NORMALISASI-FILE-KALIBRASI.txt", "a")  # append mode
            file1.write(dataLine+" \n")
            file1.close()


def generateCalData(filename,comp,ref):
    data = readCalFile(filename, comp)
    data = normalize(data,ref)
    exportToFile(data,comp)
    data = reformat(data)
    return data

def plotData(dataZ, dataN, dataE, ref):
    fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)
    fig.set_size_inches(9, 11)
    fig.suptitle("Grafik Kalibrasi Harian Survei Seismik Pasif Area Piraiba dan Tanjung Barat\n Sensor Referensi : "+ref)
    # ax1.plot(x, y)
    for key in dataZ:
        x, y = getSorted(dataZ[key][0],dataZ[key][1])
        ax1.plot(x, y, '-o', label=key)
    for key in dataN:
        x, y = getSorted(dataN[key][0],dataN[key][1])
        ax2.plot(dataN[key][0],dataN[key][1], '-o', label=key)
    for key in dataE:
        x, y = getSorted(dataE[key][0],dataE[key][1])
        ax3.plot(dataE[key][0],dataE[key][1], '-o', label=key)
    # ax1.legend()
    ax1.legend(bbox_to_anchor=(1, 1.2),ncol = len(ax1.lines))
    ax1.set_ylabel('Faktor Kalibrasi')
    ax2.set_ylabel('Faktor Kalibrasi')
    ax3.set_ylabel('Faktor Kalibrasi')
    ax1.set_title('Komponen Z')
    ax2.set_title('Komponen N')
    ax3.set_title('Komponen E')
    # ax1.yaxis.tick_right()
    # ax2.yaxis.tick_right()
    # ax3.yaxis.tick_right()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.gcf().autofmt_xdate()
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
    referenceSensor = click.prompt('Select sensor reference [GEOBIT01] ', type=str)
    clearNorfile()
    dataZ = generateCalData(filename, "Z",referenceSensor)
    dataN = generateCalData(filename, "N",referenceSensor)
    dataE = generateCalData(filename, "E",referenceSensor)
    plotData(dataZ, dataN, dataE, referenceSensor)

main.add_command(add)
main.add_command(plot)

if __name__ == '__main__':
    main()