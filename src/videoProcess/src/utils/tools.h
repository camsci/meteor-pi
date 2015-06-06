// tools.h
// Meteor Pi, Cambridge Science Centre
// Dominic Ford

#ifndef TOOLS_H
#define TOOLS_H 1

#include "vidtools/v4l2uvc.h"
#include "png/image.h"

#define CLIP256(X) ( d=X , ((d<0)?0: ((d>255)?255:d) ))

typedef struct videoMetadata
 {
  double tstart, tstop, fps, lng, lat;
  int    width, height, flagGPS, flagUpsideDown, nframe;
  char *cameraId, *videoDevice, *filename, *maskFile;
 } videoMetadata;

void  writeMetadata       (videoMetadata v);
int   nearestMultiple     (double in, int factor);
void  frameInvert         (unsigned char *buffer, int len);
void *videoRecord         (struct vdIn *videoIn, double seconds);
void  snapshot            (struct vdIn *videoIn, int nfr, int zero, double expComp, char *fname, unsigned char *medianRaw);
double calculateSkyClarity(image_ptr *img);
double estimateNoiseLevel (int width, int height, unsigned char *buffer, int Nframes);
void  medianCalculate     (const int width, const int height, const int channels, int *medianWorkspace, unsigned char *medianMap);

int dumpFrame(int width, int height, int channels, unsigned char *buffer, char *fName);
int dumpFrameFromInts(int width, int height, int channels, int *buffer, int nfr, int gain, char *fName);
int dumpFrameFromISub(int width, int height, int channels, int *buffer, int nfr, int gain, unsigned char *buffer2, char *fName);
int dumpVideo(int width, int height, unsigned char *buffer1, int buffer1frames, unsigned char *buffer2, int buffer2frames, char *fName);

#endif

