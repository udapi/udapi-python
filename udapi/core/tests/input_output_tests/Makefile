# turn it into a general cycle
# comments are exluced so that they don't have to be repeated in the output file

run:
	grep -v '^#' ../../../../../tests/test_files/remove_node.input > tmp.input
	./remove_node.py < tmp.input > tmp.output
	diff ../../../../../tests/test_files/remove_node.output tmp.output
