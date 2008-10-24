PYUIC = pyuic4
RCC = rcc

dialog_ui.py: dialog.ui
	$(PYUIC) -o $@ $^

clean:
	rm -f dialog_ui.py

