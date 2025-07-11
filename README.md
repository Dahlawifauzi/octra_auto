## _AUTO TX BANYAK WALLET KE BANYAK ADDRESS (MANY TO MANY)_

## Installation


```sh
pip install aiohttp pynacl
git clone https://github.com/Dahlawifauzi/octra_auto.git
cd octra-auto
```

edit dulu wallet.json dengan adress dan pk kelean
```sh
{
  "priv": "ISI PRIVATE KEY",
  "addr": "ISI OCTRA ADDRESS",
  "rpc": "https://octra.network"
}
```
dan edit isi address.txt yaitu address yang mau kita send/penerima 
```sh
oct4xxx1
oct4xxx2
oct4xxx3
oct4xxx4
oct4xxx5
```
## cara run pake python3 atau python
```sh
python3 send.py
```
exploler octra : https://octrascan.io/

### Note : jika di vps pas ```install pip install aiohttp pynacl``` atau error pas run ```python3 multi.py``` pake cara ini 
jika banyak wallet dan tx banyak pastikan membuat screen terlebih dahulu

```sh
sudo apt install python3-venv
```
```sh
python3 -m venv venv
```
```sh
source venv/bin/activate
```
```sh
pip install aiohttp pynacl
```
```sh
python send.py
```
