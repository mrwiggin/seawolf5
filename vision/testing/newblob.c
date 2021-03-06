
#include <seawolf.h>

#include <cv.h>
#include <highgui.h>

typedef uint32_t BlobId;

typedef struct Blob_s {
    BlobId id;

    /* If size == -1 then the blob is no longer valid. This is set when two
       blobs are joined. Otherwise, this gives the size of the blob in pixels */
    int32_t size;

    /* Centroid */
    uint32_t c_x;
    uint32_t c_y;

    /* Bound box */
    uint16_t x_0;
    uint16_t x_1;
    uint16_t y_0;
    uint16_t y_1;
} Blob;

Blob** find_blobs(IplImage* img_in, IplImage* blobs_out, int* r_num_blobs, int min_size, int keep_number);
void free_blobs(Blob** blobs, int num_blobs);

int main(int argc, char** argv) {
    IplImage* img_in = cvLoadImage(argv[1], CV_LOAD_IMAGE_GRAYSCALE);
    IplImage* binary = cvCreateImage(cvGetSize(img_in), 8, 1);

    Timer* t = Timer_new();
    double time;

    Blob** blobs;
    int num_blobs;

    cvAdaptiveThreshold(img_in, binary, 255, CV_ADAPTIVE_THRESH_MEAN_C, CV_THRESH_BINARY_INV, 7, 20);
//    cvShowImage("input", binary);

    while(cvWaitKey(1) != 'q') {
        Timer_reset(t);
        blobs = find_blobs(binary, binary, &num_blobs, 25, 255);
        time = Timer_getDelta(t);

        printf("(%.4f) Found %d blobs\n", time, num_blobs);
        free_blobs(blobs, num_blobs);
//        cvShowImage("output", binary);
    }

    return 0;
}
