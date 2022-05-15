# A collection of cnvrg libhub libraries

### Development Installation Instructions
- brew install pyenv
- pyenv install 3.8.0
```
  MIGHT NEED TO RUN BIG SUR PATCH:
  CFLAGS="-I$(brew --prefix openssl)/include -I$(brew --prefix bzip2)/include -I$(brew --prefix readline)/include -I$(xcrun --show-sdk-path)/usr/include" LDFLAGS="-L$(brew --prefix openssl)/lib -L$(brew --prefix readline)/lib -L$(brew --prefix zlib)/lib -L$(brew --prefix bzip2)/  CFLAGS="-I$(brew --prefix openssl)/include -I$(brew --prefix bzip2)/include -I$(brew --prefix readline)/include -I$(xcrun --show-sdk-path)/usr/include" LDFLAGS="-L$(brew --prefix openssl)/lib -L$(brew --prefix readline)/lib -L$(brew --prefix zlib)/lib -L$(brew --prefix bzip2)/lib" pyenv install --patch 3.9.0 < <(curl -sSL https://github.com/python/cpython/commit/8ea6353.patch\?full_index\=1) lib" pyenv install --patch 3.9.0 < <(curl -sSL https://github.com/python/cpython/commit/8ea6353.patch\?full_index\=1)
```
- git clone git@github.com:AccessibleAI/cnvrg-libhub-libraries.git

#### Note that each library has its own requirements and will need to be installed separately!

### Creating a new library
- Create a new python package (with __init__.py file)
- Setup python environment (DO NOT USE A GLOBAL ENV!)
  - cd <your_library>
  - python3 -m venv venv
  - source venv/bin/activate
- Add README.md + requirements.txt + library.yaml
- When installing a new requirements please use `pip install <pkg> && pip freeze > requirements.txt`