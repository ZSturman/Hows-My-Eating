# How's My Eating?

## A Real-Time Solution to Slow Down Binge Eating

### Overview

**How's My Eating?** is an iOS application designed to help users develop healthier eating habits by slowing down their eating pace. The app leverages kinetic data collected from devices like AirPods to monitor your eating speed and provide real-time notifications if you’re eating too fast. The goal is to help users avoid binge eating, improve digestion, and increase the enjoyment of food.

### Background

The habit of binge eating, often exacerbated by distractions like television, can make it difficult to listen to the body’s signals of fullness. Recognizing the challenges of breaking this habit, I've decided to develop an app that would gently remind users to slow down and savor their meals.

### Benefits of Slowing Down

- **Mindful Eating**: Encourages healthier food choices.
- **Prevent Overeating**: Helps you listen to your body and stop eating when full.
- **Enhanced Enjoyment**: Improves the quality of life by allowing you to fully taste and enjoy your food.

### App Features

- **Real-Time Notifications**: The app monitors your eating pace or chew count and sends notifications to your phone or watch, prompting you to slow down if necessary.
- **Kinetic Data Monitoring**: Utilizes AirPods to capture rotation rate and other kinetic data, determining whether your mouth is open or closed—a key indicator of eating pace.
- **Privacy-Friendly**: Focuses on kinetic data to provide a less intrusive solution for users who value their privacy.

### Development Process

#### Data Collection

- Currently, the app is in the data collection phase, recording audio, visual, and kinetic data related to eating habits.
- Data is being collected by Zachary using the iOS app, which will soon be available for download.

#### Data Labeling

- A system is being developed for labeling the collected data.
- FastHTML is being considered as the framework to facilitate this process.

#### Model Training

- **Initial Approach**: Google's Teachable Machine is being used for initial model training due to its simplicity.
- **Advanced Frameworks**: Depending on the initial results, the plan is to transition to more robust frameworks like PyTorch or CoreML for enhanced model accuracy.

#### App Development

- **Model Integration**: Once the model is trained, it will be integrated into the iOS app.
- **Real-Time Detection**: The app will be capable of detecting eating habits using kinetic data alone.
- **User Notifications**: If the app detects fast eating habits, it will send real-time notifications to your phone or watch, reminding you to slow down.

### Next Steps

- **App Launch**: The app is still in development, with plans to make it available for download soon.
- **Community Involvement**: Interested users and developers can follow along or contribute to the project by checking out the GitHub repository once it goes live.

### Connect with Me

You can find me at [Zachary-Sturman.com](zachary-sturman.com), [email me directly](zasturman@gmail.com), or on the following platforms:

- [LinkedIn](https://www.linkedin.com/in/zacharysturman/)
- [GitHub](https://github.com/ZSturman)
- [Hashnode](https://zacharysturman.hashnode.dev/)
- [Dev.to](https://dev.to/zacharysturman)
- [X / Twitter](https://twitter.com/zachary_sturman)
- [Bluesky](https://bsky.app/profile/zacharysturman.bsky.social)

---

Stay up to date by subscribing to the articles at [zacharysturman.hashnode.dev](https://zacharysturman.hashnode.dev/hows-my-eating)
