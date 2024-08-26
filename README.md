# Downloader Z
Downloader Z is a Python-based downloader with advanced features such as custom chunk sizes, file integrity verification (MD5), decryption, extraction of .7z files, and support for command-line arguments and JSON configuration files for instant downloads.

## Features
- **Custom Chunk Sizes**: Optimize download speed and performance by specifying custom chunk sizes.

- **File Integrity Verification**: Ensure file integrity with MD5 checksum verification.
- **Decryption of 7z Files**: Automatically decrypt .7z files after download.
- **Extraction of 7z Files**: Automatically extract contents from downloaded .7z files.
- **Command Line Support**: Fully-featured command-line interface for managing downloads.
- **JSON Configuration Support**: Load download configurations from JSON files for quick and easy setup.
## Installation
1. Clone the repository : 

```
git clone https://github.com/AnonymCodeGit15/Downloader_Z.git
cd Downloader_Z
```
2. Install the dependencies
`pip install -r requirements.txt`

3. Paste the Google cloud service account credentials in a file named `creds.json`  in the same directory as `Downloader_Z.py`

## Usage

### Json file usage 
Save the configuration parameters in a json file named `config_down.json` in the same directory as `Downloader_Z.py`

 Example JSON file ( default test 50Mb file ): 
 ```
 {
  "id": "1wm79RcJfBmGKaxnWNKDCNNlvIbI2JiDy",
  "folder_out": "Download",
  "file_out" : "test_down.7z",
  "md5" : "ee99f11231036576d71eb5a37a627825",
  "password" : ""
}
```

> [!NOTE]
> The md5 and password can be left as empty ie as  `""` to skip checksum verification or to extract unencrypted files respectively. 

> [!CAUTION]
> The JSON file named config_down.json is automatically loaded without passing any command line arguments.

### Command line arguments usage 
Example command line based usage ( default test 50Mb file ) : 
```
./Downloader_Z.py --id "1wm79RcJfBmGKaxnWNKDCNNlvIbI2JiDy" --folder_out "Download" --file_out "test_down.7z" --md5 "ee99f11231036576d71eb5a37a627825"
```
## License
[GNU LGPLv3](https://choosealicense.com/licenses/lgpl-3.0/)

