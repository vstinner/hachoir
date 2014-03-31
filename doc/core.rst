++++
core
++++

Why using slow Python code instead of fast hardcoded C code? Hachoir has many
interesting features:

* Autofix: Hachoir is able to open invalid / truncated files
* Lazy: Open a file is very fast since no information is read from file,
  data are read and/or computed when the user ask for it
* Types: Hachoir has many predefined field types (integer, bit, string, etc.)
  and supports string with charset (ISO-8859-1, UTF-8, UTF-16, ...)
* Addresses and sizes are stored in bit, so flags are stored as classic fields
* Endian: You have to set endian once, and then number are converted in the
  right endian
* Editor: Using Hachoir representation of data, you can edit, insert, remove
  data and then save in a new file.

Pages:

* [[Features|Feature list]]
* [[QualityControl|Quality control]]: documentation, diagrams, ...
* [[WhatsNew|What's New]]
* [[Limits|Hachoir limits]]

