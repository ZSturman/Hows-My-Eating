import { useLabelContext } from '../context/LabellingContext';

const LabellingAndPlayback = () => {
  const { state } = useLabelContext();

  return (
    <div className="flex flex-col items-center justify-center w-full">

      <div className="flex flex-row w-full max-w-full items-start">

          {!state.movPath && (
            <p>Loading video...</p>
          )}
        </div>

    </div>
  );
};

export default LabellingAndPlayback;