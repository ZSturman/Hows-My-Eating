type MotionData = {
    timestamp: number;
    attitude: {
        pitch: number;
        roll: number;
        yaw: number;
    };
    userAcceleration: {
        x: number;
        y: number;
        z: number;
    };
    rotationRate: {
        x: number;
        y: number;
        z: number;
    };
    gravity: {
        x: number;
        y: number;
        z: number;
    };
};

type MotionPlayerProps = {
    data: MotionData[];
};


type LabelledData = MotionData & {
    primaryLabel: string;
    secondaryLabel: string;
    bodyActivity: string;
    mouthActivity: string;
}



type RecordedAndLabelledData = {
    jsonData: MotionData[];
    moviePath: string;
    labelledData?: LabelledData[];
}

type FlashMessage = {
    title: string;
    message: string;
    type: 'success' | 'error' | 'info' | 'warning';
}
