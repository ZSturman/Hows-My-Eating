type LabellerProps = {
  labelData: LabelledData[] | null;
};

const Labeller: React.FC<LabellerProps> = ({ labelData }) => {
  return (
    <div>
      <h2>Labeller</h2>
      <pre>{JSON.stringify(labelData, null, 2)}</pre>
    </div>
  );
}

export default Labeller