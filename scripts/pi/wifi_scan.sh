sudo sh -c 'ifconfig wlan0 up && iwlist wlan0 scanning' | awk 'BEGIN{ FS="[:=]"; OFS = " " }
/ESSID/{
    essid[c++]=$2
}
/Frequency/{
    gsub(/ \(Channel .*\)/,"")
    gsub(/ GHz/,"")
    frequency[e++]=$2
}
/Channel/{
    channel[f++]=$2
}
/Address/{
    gsub(/.*Address: /,"")
    address[a++]=$0
}
/Encryption key/{
    encryption[d++]=$2
}
/Quality/{
    gsub(/ dBm  /,"")
    signal[b++]=$3
}
END {
    for( c in essid ) {
        print address[c],essid[c],frequency[c],channel[c],signal[c],encryption[c]
    }
}'