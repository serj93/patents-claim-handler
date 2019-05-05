import pprint as pp
import time, argparse, sys, os.path

from tools.patenthandler import PatentHandler

def check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("{} is an invalid positive int value".format(value))
    return ivalue

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Generate RDF-data of devices from XML patent docs.')

    subparsers = parser.add_subparsers(help='Mode selection')
    parser_b = subparsers.add_parser('batch', help='Batch mode')
    parser_b.add_argument('-i', '--input', help='Input directory (patent docs)', required=True)
    parser_b.add_argument('-o', '--output', help='Output directiory (owl files)', required=True)
    parser_b.add_argument('-l', '--limit', help='Max docs to be processed (with data)', type=check_positive, default=1000)
    parser_b.add_argument('-c', '--chunksize', help='Max docs per OWL-file', type=check_positive, default=500)

    parser_s = subparsers.add_parser('single', help='Single mode')
    parser_s.add_argument('-p', '--patent', help='Input Patent file name', required=True)
    parser_s.add_argument('-o', '--owl', help='Output OWL file name')
    parser_s.add_argument("-g", "--print_graph", action="store_true", help='Print graph of invention')

    args = parser.parse_args()
    args_keys = vars(args).keys()
    
    # Check params!
    if not ('input' in args_keys or 'patent' in args_keys):
        parser.print_help()
        sys.exit(1)

    is_single_mode = 'patent' in args_keys

    phandler = PatentHandler()

    if is_single_mode:
        if not os.path.isfile(args.patent):
            print("\nError!!! File not found.\n")
            parser_s.print_help()
            sys.exit(1)
        print("Start single processing ...")
        phandler.patentSingleProcessing(args.patent, args.owl, args.print_graph)
    else:
        if not os.path.exists(args.input):
            print("\nError!!! Input directory unavailable.\n")
            parser_b.print_help()
            sys.exit(1)

        if not os.path.exists(args.output):
            print("\nError!!! Output directory unavailable.\n")
            parser_b.print_help()
            sys.exit(1)

        print("Start butch processing ...")
        start_time = time.time()
        phandler.patentBatchProcessing(args.input, args.output, args.limit, args.chunksize)
        print("\nProcessing time: {} sec.".format(time.time() - start_time))

    print("\nFinish.")
