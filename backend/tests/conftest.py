import os,tempfile
# Set the test store before any application module is imported during collection.
os.environ['MULTIVARIAT_DATA']=tempfile.mkdtemp(prefix='multivariat-test-')
