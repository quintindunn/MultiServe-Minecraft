# Setup
## Python:
- Install [python3](https://www.python.org/downloads/) from https://www.python.org/downloads/
- Install requirements with `python3 -m pip install -r requirements.txt`
## Java:
1. Download [Java 8](https://www.azul.com/downloads/?version=java-8-lts&package=jdk&show-old-builds=true) from https://www.azul.com/downloads/?version=java-8-lts&package=jdk&show-old-builds=true
   - Save the directory with the `java.exe` for Java 8 e.g. `C:\Program Files\Zulu\zulu-8\bin` to `JAVA_JDK8` in `config.py`
2. Download [Java JDK 16](https://www.azul.com/downloads/?version=java-16-sts&package=jdk&show-old-builds=true) from https://www.azul.com/downloads/?version=java-16-sts&package=jdk&show-old-builds=true
   - Save the directory with the `java.exe` for Java JDK 16 e.g. `C:\Program Files\Zulu\zulu-16\bin` to `JAVA_JDK16` in `config.py`
3. Download [Java JDK 17](https://www.azul.com/downloads/?package=jdk#download-openjdk) from https://www.azul.com/downloads/?package=jdk#download-openjdk
   - Save the directory with the `java.exe` for Java JDK 17 e.g. `C:\Program Files\Zulu\zulu-17\bin` to `JAVA_JDK17` in `config.py`
   - Make sure JDK 17 is the highest in your path, (Newer JDK versions i.e. JDK 18 will work too)