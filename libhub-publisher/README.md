# Libhub Publisher
This is a utility library that is used to create blueprints from flows.


### Example usage
- Create a new cnvrg project
- Inside the project files create a folder - This folder will represent a library
- Inside the folder add the following files:
  - README.md - The readme will contain information about your library
  - requirements.txt - The requirements file will contain all of your library requirements
  - \_\_init\_\_.py - Optional file to mark your library as a package
  - [main].py - The entrypoint file (can be any filename)
- Create a new flow:
  - Give it a title - the title will be your blueprint name (and its slug will be all lowercase and dashes instead of spaces)
  - Create a new task and connect it to the library folder using the "library info" tab
  - **Only library tasks (either from libhub or a folder) are supported in a blueprint flow**
- Run the flow - You can add more tasks and tweak your code until your flow works as expected.
- Publish the flow - Once everything works to your satisfaction you can hit "Publish" which will run and validate your entire flow and afterwards will run this library in order to upload your flow to libhub with all of the relevant libraries