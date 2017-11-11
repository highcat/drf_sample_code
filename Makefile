clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '.\#*' -exec rm -f {} +
	find . -name '\#*\#' -exec rm -f {} +
	find . -depth -type d -empty -delete
