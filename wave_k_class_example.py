import argparse
from waveform_generator import Agilent33220A

AGILENT_IP = "192.168.0.210"


def main():
    parser = argparse.ArgumentParser(description="Waveform generator control")
    parser.add_argument("--mode", type=int, default=0,
                        help="0=ramp, 1=square, 2=DC, 3=two square, 4=two ramp")
    parser.add_argument("--freq", type=float, default=10)
    parser.add_argument("--amp", type=float, default=5)
    parser.add_argument("--offset", type=float, default=0)
    parser.add_argument("--sym", type=float, default=50)
    args = parser.parse_args()

    wave = Agilent33220A(AGILENT_IP)

    try:
        wave.connect()

        if args.mode == 0:
            wave.set_ramp(args.freq, args.amp, args.offset, args.sym, channel=1)
            wave.output_on(1)
        elif args.mode == 1:
            wave.set_square(args.freq, args.amp, args.offset, channel=1)
            wave.output_on(1)
        elif args.mode == 2:
            wave.set_dc(args.offset, channel=1)
            wave.output_on(1)
        elif args.mode == 3:
            wave.set_square(args.freq, args.amp, args.offset, channel=1)
            wave.set_square(args.freq, args.amp, args.offset, channel=2)
            wave.output_on(1)
            wave.output_on(2)
        elif args.mode == 4:
            wave.set_ramp(args.freq, args.amp, args.offset, args.sym, channel=1)
            wave.set_ramp(args.freq, args.amp, args.offset, args.sym, channel=2)
            wave.output_on(1)
            wave.output_on(2)
        else:
            raise ValueError("mode must be 0, 1, 2, 3, or 4")

        print("Waveform output configured.")
    finally:
        wave.close()


if __name__ == "__main__":
    main()
