# GOOSE and where it fits — background for the CITS3200 RADAR project

Written for anyone joining this work — including next year's team. Assumes no prior
knowledge of autonomous driving. Quotes from Adrian and Fabian are from the kickoff
meeting transcript of 4 August 2026.

---

## 1. What the project actually is

Adrian set the tone in the first two minutes:

> *"This project is a little bit loosely defined. It's really just — I don't know
> anything about radar, he doesn't really know much about radar, we like trucks and
> robots and we think they're cool, and so it's an area that we're trying to get
> ourselves a bit up to speed on."*

It is a **learning and benchmarking exercise**, not a product build. Three parts:

1. Understand the self-driving stack and how the sensor types differ
2. Focus in on trucks, and on 4D radar specifically — both very new
3. Benchmark: if you try to detect something using LiDAR, versus a camera, versus
   radar, how do they differ? What are the pros and cons?

The method Adrian described:

> *"We would find some open source solutions that are out there, some other research
> groups have tried, make a big collection of them, and basically we're just trying to
> run them on the data sets. So okay, we ran this algorithm, we spent X number of days
> trying to get it going, we couldn't get it going — or yep, we got it working but it
> doesn't perform very well."*

Note what counts as success there. **"We could not get it working" is a reportable
result.** That is why this repo records failures as first-class outcomes.

---

## 2. Where datasets sit in the stack

An autonomous driving system runs roughly:

```
sensors  →  PERCEPTION  →  prediction  →  planning  →  control
```

- **Sensors** — cameras, LiDAR, radar, GPS/IMU
- **Perception** — turning raw readings into "there is a tree 12 m ahead", or "this
  patch of ground is drivable"
- **Prediction / planning / control** — what will move where, what should we do, and
  actually steering

**This project lives entirely in perception.** You are not building planning or control.

The problem: you cannot test perception by driving a truck around a mine site. So the
field uses **datasets**. Someone already drove a sensor-covered vehicle around,
recorded everything, and paid people to label what is in each frame. A dataset gives
you three things:

1. **Frozen sensor recordings** — images, LiDAR point clouds, radar returns
2. **Ground truth** — a human's answer for what is actually there
3. **A devkit** — code to load it all

You run a model on (1), compare its output against (2), and get a score. That is
benchmarking, and it is what this project does.

**Autoware** sits alongside as an open-source implementation of the *whole* stack. You
can replay a dataset into it and watch the pipeline run — which is why "does this
dataset ship ROS bags" is a question worth asking.

---

## 3. The one concept that makes GOOSE make sense

**Object detection** asks *"where are the things?"*
Output: a list of 3D boxes — car here, pedestrian there. Scored with **mAP**.
This is what MAN TruckScenes and TruckDrive do.

**Semantic segmentation** asks *"what is everything made of?"*
Output: a class label for every pixel and every LiDAR point. Scored with **mIoU**.
This is what GOOSE does.

They are not interchangeable and **their scores cannot go in the same table**. That is
what decision D-01 in `decision-log.md` protects against.

Why it matters: on a highway, detection is the right question — there are discrete
objects and you need boxes around them. Off-road, in a forest or a mine, detection is
close to useless. There are no lanes and often no other vehicles. The real question is
**"can I drive on this?"** — a per-point question about terrain. That is segmentation.

---

## 4. What GOOSE is

The **German Outdoor and Offroad Dataset**, Fraunhofer IOSB and partners, ICRA 2024.

A research vehicle (MuCAR-3) drove around forests, fields, campus grounds and gravel
tracks across all four seasons and varied weather, with LiDAR and cameras running.
Humans then labelled **10,000 frames** — every pixel of the image and every point of
the LiDAR cloud — into **64 classes**.

Look at what those classes are:

> `low_grass` · `high_grass` · `bush` · `moss` · `leaves` · `soil` · `gravel` ·
> `cobble` · `asphalt` · `snow` · `tree_root` · `tree_trunk` · `rock` · `water` ·
> `debris` · `fence`

Now compare that with what Adrian said they care about:

> *"For a self-driving system, understanding the ground — what is ground, what is not
> the ground? **What can I drive over? What can I crash into?** ... In an open
> environment or a mining environment, **there is an edge and you can drive off it and
> we don't want to crash.**"*

**GOOSE's 64 classes are an enumeration of exactly that question.** `low_grass` — drive
over it. `high_grass` — probably, but you cannot see what is underneath. `bush` —
maybe. `tree_trunk` — you will crash. `water` — do not. That is the design intent of
the dataset.

This is why Fabian named GOOSE at the kickoff, and why Adrian's email of 11 August said
other datasets are welcome *"IN ADDITION to GOOSE — but not eliminating GOOSE."* It is
the dataset-shaped version of the problem they find interesting.

### The facts

| | |
|---|---|
| Task | Semantic segmentation, 2D and 3D — **no 3D bounding boxes** |
| Labelled frames | 10,000 of 15,000 total (train 7,830 / val 960 / test 1,210) |
| Classes | 64 |
| Sensors labelled | RGB images and LiDAR point clouds only |
| Sensors on the vehicle | 3 LiDAR, 7 cameras (incl. NIR + thermal), **6 radar**, INS/GNSS |
| Licence | CC BY-SA 4.0 data, MIT devkit — **the most permissive dataset we have** |
| Size | ~62 GB total; validation split 3.3 GB |
| Distribution | Annotated zips, plus raw **ROS 1** bags |

Full detail in [`../docs/dataset-surveys/goose.md`](../docs/dataset-surveys/goose.md).

---

## 5. The radar situation — read this carefully

GOOSE's vehicle carries **six radar sensors** giving 360° coverage: five Smartmicro
UMRR-96 (79 GHz, 0.4–55 m) and one UMRR-11 (77 GHz, 1–175 m). This is documented in
the paper's platform section.

But there are three problems:

1. **The radar is not labelled.** Only images and LiDAR carry ground truth.
2. **The radar is not in the annotated download.** It exists only in the raw ROS bags.
3. **The released bags carry a reduced sensor set.** The dataset authors confirmed this
   directly: *"the ROS Bags available on the GOOSE DB only contain a minimal set of
   sensors to reduce the file sizes... We are still in the process of uploading and
   releasing the full raw sensor data."* A user checking the bags found even the
   surround cameras missing. The torrent has no seeders.

On top of that, the paper never describes the radars as **4D imaging** — and their
ranges suggest conventional automotive radar.

**Conclusion: GOOSE cannot answer the radar question, and should not be planned as if
it could.** That is not a failure of the dataset; it is a division of labour. See §6.

> An earlier draft of our survey said GOOSE had *no* radar. That came from reading the
> project landing page, which lists only the annotated modalities. The correction is
> kept visible in the survey rather than quietly edited out.

---

## 6. What each dataset is for

The four datasets are **not competing candidates**. They are different instruments, and
each answers one question.

| Dataset | The question it answers | Task | Status |
|---|---|---|---|
| **MAN TruckScenes** | Radar vs LiDAR vs camera, like-for-like — 6 radar + 6 LiDAR + shared 3D boxes on the same scenes | Detection | Available |
| **TruckDrive** | Does perception collapse beyond ~150 m? (decision D-04) | Detection to 400 m | Available, licence-gated |
| **GOOSE** | Can we tell drivable ground from obstacles, off-road? | Segmentation | **Working — data loaded** |
| **STONE** | Both at once: off-road *and* annotated 4D radar | Traversability | Parked — 322 GiB, no devkit |

**TruckScenes** is the core modality comparison, because it is the only dataset where
radar and LiDAR see the same scenes with the same ground truth. **TruckDrive** is where
the interesting failure happens — published results show 31–99% degradation past 150 m.
**GOOSE** is the client's actual interest, and the only one you can work on today.
**STONE** would have bridged off-road and radar, which is why it is worth chasing
storage for.

---

## 7. So what is GOOSE *for*?

**Three real jobs:**

1. **The off-road terrain baseline.** Separating drivable ground from obstacles. This
   is the client's stated interest and the only dataset that can do it today.
2. **The on-road → off-road transfer testbed.** Fabian said this explicitly: *"it would
   be very interesting to see the transfer from when you train models on the normal
   road, how it transfers to these off-road environments."* GOOSE is the off-road end.
3. **The Autoware entry point.** It is the only dataset here that ships native ROS
   bags. Everything else would need a converter written from scratch — `DATASET_OVERVIEW.md`
   records that no TruckScenes→ROS 2 converter exists. Caveat: GOOSE's bags are ROS 1,
   so conversion is still needed, just far less of it.

**One job it cannot do:** tell you whether radar beats LiDAR. Do not plan around it.

---

## 8. Known limitations

Before building anything on GOOSE:

- **Camera and LiDAR are not reliably time-aligned.** The authors confirmed a bug in
  their export step; ground-truth masks for the camera and LiDAR of the same frame
  cannot be matched by projection using the published extrinsics. **Sensor fusion on
  this data will produce broken results through no fault of yours.**
- Some LiDAR scans are missing sections; at least one RGB frame is out of sequence.
- Two different taxonomies ship with the dataset — the full 64-class set and an
  8-class challenge remap. They are not interchangeable, and any reported number must
  say which it used.
- Labelled points extend to roughly **±200 m** (measured, not published), but density
  at that range is sparse.

---

## 9. Where this sits in the assessment

The project's own framing, from the Sprint 1 documents:

- **Epic B** (Damien) — fundamentals, off-road domain, benchmarking infrastructure
- **DZ-2** — the off-road dataset catalogue, which GOOSE and STONE satisfy
- **Decision D-03** — the off-road direction. Its Sprint-1 premise was that off-road
  datasets carry no radar. **That premise is false**: STONE has annotated 4D radar and
  GOOSE has raw radar. D-05 records the correction.
- **Risk R-24** (Damien) — whether an off-road dataset with radar exists at all

And Adrian's guidance on how to work, which is worth remembering when a fortnight feels
slow:

> *"I would suggest doing that for the first four to six weeks or something, until you
> get the hang of what's all going here. And then at that point... you come together as
> a group and say, okay, this is what a solid product would look like."*
