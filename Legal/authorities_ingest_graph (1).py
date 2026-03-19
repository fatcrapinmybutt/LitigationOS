#!/usr/bin/env python2
# encoding: UTF-8
import json
import sys

sys.path.append("./")
import zipfile
import re
import sys
import os
import codecs
import traceback
import numpy as np
from utils import order_points_clockwise


def print_help():
    sys.stdout.write(
        "Usage: python %s.py -g=<gtFile> -s=<submFile> [-o=<outputFolder> -p=<jsonParams>]"
        % sys.argv[0]
    )
    sys.exit(2)


def load_zip_file_keys(file, fileNameRegExp=""):
    """
    Returns an array with the entries of the ZIP file that match with the regular expression.
    The key's are the names or the file or the capturing group defined in the fileNameRegExp
    """
    try:
        archive = zipfile.ZipFile(file, mode="r", allowZip64=True)
    except:
        raise Exception("Error loading the ZIP archive.")

    pairs = []

    for name in archive.namelist():
        addFile = True
        keyName = name
        if fileNameRegExp != "":
            m = re.match(fileNameRegExp, name)
            if m == None:
                addFile = False
            else:
                if len(m.groups()) > 0:
                    keyName = m.group(1)

        if addFile:
            pairs.append(keyName)

    return pairs


def load_zip_file(file, fileNameRegExp="", allEntries=False):
    """
    Returns an array with the contents (filtered by fileNameRegExp) of a ZIP file.
    The key's are the names or the file or the capturing group defined in the fileNameRegExp
    allEntries validates that all entries in the ZIP file pass the fileNameRegExp
    """
    try:
        archive = zipfile.ZipFile(file, mode="r", allowZip64=True)
    except:
        raise Exception("Error loading the ZIP archive")

    pairs = []
    for name in archive.namelist():
        addFile = True
        keyName = name
        if fileNameRegExp != "":
            m = re.match(fileNameRegExp, name)
            if m == None:
                addFile = False
            else:
                if len(m.groups()) > 0:
                    keyName = m.group(1)

        if addFile:
            pairs.append([keyName, archive.read(name)])
        else:
            if allEntries:
                raise Exception("ZIP entry not valid: %s" % name)

    return dict(pairs)


def load_folder_file(file, fileNameRegExp="", allEntries=False):
    """
    Returns an array with the contents (filtered by fileNameRegExp) of a ZIP file.
    The key's are the names or the file or the capturing group defined in the fileNameRegExp
    allEntries validates that all entries in the ZIP file pass the fileNameRegExp
    """
    pairs = []
    for name in os.listdir(file):
        addFile = True
        keyName = name
        if fileNameRegExp != "":
            m = re.match(fileNameRegExp, name)
            if m == None:
                addFile = False
            else:
                if len(m.groups()) > 0:
                    keyName = m.group(1)

        if addFile:
            pairs.append([keyName, open(os.path.join(file, name)).read()])
        else:
            if allEntries:
                raise Exception("ZIP entry not valid: %s" % name)

    return dict(pairs)


def decode_utf8(raw):
    """
    Returns a Unicode object on success, or None on failure
    """
    try:
        raw = codecs.decode(raw, "utf-8", "replace")
        # extracts BOM if exists
        raw = raw.encode("utf8")
        if raw.startswith(codecs.BOM_UTF8):
            raw = raw.replace(codecs.BOM_UTF8, "", 1)
        return raw.decode("utf-8")
    except:
        return None


def validate_lines_in_file(
    fileName,
    file_contents,
    CRLF=True,
    LTRB=True,
    withTranscription=False,
    withConfidence=False,
    imWidth=0,
    imHeight=0,
):
    """
    This function validates that all lines of the file calling the Line validation function for each line
    """
    utf8File = decode_utf8(file_contents)
    if utf8File is None:
        raise Exception("The file %s is not UTF-8" % fileName)

    lines = utf8File.split("\r\n" if CRLF else "\n")
    for line in lines:
        line = line.replace("\r", "").replace("\n", "")
        if line != "":
            try:
                validate_tl_line(
                    line, LTRB, withTranscription, withConfidence, imWidth, imHeight
                )
            except Exception as e:
                raise Exception(
                    (
                        "Line in sample not valid. Sample: %s Line: %s Error: %s"
                        % (fileName, line, str(e))
                    ).encode("utf-8", "replace")
                )


def validate_tl_line(
    line, LTRB=True, withTranscription=True, withConfidence=True, imWidth=0, imHeight=0
):
    """
    Validate the format of the line. If the line is not valid an exception will be raised.
    If maxWidth and maxHeight are specified, all points must be inside the image bounds.
    Possible values are:
    LTRB=True: xmin,ymin,xmax,ymax[,confidence][,transcription]
    LTRB=False: x1,y1,x2,y2,x3,y3,x4,y4[,confidence][,transcription]
    """
    get_tl_line_values(line, LTRB, withTranscription, withConfidence, imWidth, imHeight)


def get_tl_line_values(
    line,
    LTRB=True,
    withTranscription=False,
    withConfidence=False,
    imWidth=0,
    imHeight=0,
):
    """
    Validate the format of the line. If the line is not valid an exception will be raised.
    If maxWidth and maxHeight are specified, all points must be inside the image bounds.
    Possible values are:
    LTRB=True: xmin,ymin,xmax,ymax[,confidence][,transcription]
    LTRB=False: x1,y1,x2,y2,x3,y3,x4,y4[,confidence][,transcription]
    Returns values from a textline. Points , [Confidences], [Transcriptions]
    """
    confidence = 0.0
    transcription = ""
    points = []

    numPoints = 4

    if LTRB:
        numPoints = 4

        if withTranscription and withConfidence:
            m = re.match(
                r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-1].?[0-9]*)\s*,(.*)$",
                line,
            )
            if m == None:
                m = re.match(
                    r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-1].?[0-9]*)\s*,(.*)$",
                    line,
                )
                raise Exception(
                    "Format incorrect. Should be: xmin,ymin,xmax,ymax,confidence,transcription"
                )
        elif withConfidence:
            m = re.match(
                r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-1].?[0-9]*)\s*$",
                line,
            )
            if m == None:
                raise Exception(
                    "Format incorrect. Should be: xmin,ymin,xmax,ymax,confidence"
                )
        elif withTranscription:
            m = re.match(
                r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,(.*)$",
                line,
            )
            if m == None:
                raise Exception(
                    "Format incorrect. Should be: xmin,ymin,xmax,ymax,transcription"
                )
        else:
            m = re.match(
                r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,?\s*$",
                line,
            )
            if m == None:
                raise Exception("Format incorrect. Should be: xmin,ymin,xmax,ymax")

        xmin = int(m.group(1))
        ymin = int(m.group(2))
        xmax = int(m.group(3))
        ymax = int(m.group(4))
        if xmax < xmin:
            raise Exception("Xmax value (%s) not valid (Xmax < Xmin)." % (xmax))
        if ymax < ymin:
            raise Exception("Ymax value (%s)  not valid (Ymax < Ymin)." % (ymax))

        points = [float(m.group(i)) for i in range(1, (numPoints + 1))]

        if imWidth > 0 and imHeight > 0:
            validate_point_inside_bounds(xmin, ymin, imWidth, imHeight)
            validate_point_inside_bounds(xmax, ymax, imWidth, imHeight)

    else:
        numPoints = 8

        if withTranscription and withConfidence:
            m = re.match(
                r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-1].?[0-9]*)\s*,(.*)$",
                line,
            )
            if m == None:
                raise Exception(
                    "Format incorrect. Should be: x1,y1,x2,y2,x3,y3,x4,y4,confidence,transcription"
                )
        elif withConfidence:
            m = re.match(
                r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-1].?[0-9]*)\s*$",
                line,
            )
            if m == None:
                raise Exception(
                    "Format incorrect. Should be: x1,y1,x2,y2,x3,y3,x4,y4,confidence"
                )
        elif withTranscription:
            m = re.match(
                r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,(.*)$",
                line,
            )
            if m == None:
                raise Exception(
                    "Format incorrect. Should be: x1,y1,x2,y2,x3,y3,x4,y4,transcription"
                )
        else:
            m = re.match(
                r"^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*$",
                line,
            )
            if m == None:
                raise Exception("Format incorrect. Should be: x1,y1,x2,y2,x3,y3,x4,y4")

        points = [float(m.group(i)) for i in range(1, (numPoints + 1))]

        points = order_points_clockwise(np.array(points).reshape(-1, 2)).reshape(-1)
        validate_clockwise_points(points)

        if imWidth > 0 and imHeight > 0:
            validate_point_inside_bounds(points[0], points[1], imWidth, imHeight)
            validate_point_inside_bounds(points[2], points[3], imWidth, imHeight)
            validate_point_inside_bounds(points[4], points[5], imWidth, imHeight)
            validate_point_inside_bounds(points[6], points[7], imWidth, imHeight)

    if withConfidence:
        try:
            confidence = float(m.group(numPoints + 1))
        except ValueError:
            raise Exception("Confidence value must be a float")

    if withTranscription:
        posTranscription = numPoints + (2 if withConfidence else 1)
        transcription = m.group(posTranscription)
        m2 = re.match(r"^\s*\"(.*)\"\s*$", transcription)
        if (
            m2 != None
        ):  # Transcription with double quotes, we extract the value and replace escaped characters
            transcription = m2.group(1).replace("\\\\", "\\").replace('\\"', '"')

    return points, confidence, transcription


def validate_point_inside_bounds(x, y, imWidth, imHeight):
    if x < 0 or x > imWidth:
        raise Exception(
            "X value (%s) not valid. Image dimensions: (%s,%s)"
            % (xmin, imWidth, imHeight)
        )
    if y < 0 or y > imHeight:
        raise Exception(
            "Y value (%s)  not valid. Image dimensions: (%s,%s) Sample: %s Line:%s"
            % (ymin, imWidth, imHeight)
        )


def validate_clockwise_points(points):
    """
    Validates that the points that the 4 points that dlimite a polygon are in clockwise order.
    """

    if len(points) != 8:
        raise Exception("Points list not valid." + str(len(points)))

    point = [
        [int(points[0]), int(points[1])],
        [int(points[2]), int(points[3])],
        [int(points[4]), int(points[5])],
        [int(points[6]), int(points[7])],
    ]
    edge = [
        (point[1][0] - point[0][0]) * (point[1][1] + point[0][1]),
        (point[2][0] - point[1][0]) * (point[2][1] + point[1][1]),
        (point[3][0] - point[2][0]) * (point[3][1] + point[2][1]),
        (point[0][0] - point[3][0]) * (point[0][1] + point[3][1]),
    ]

    summatory = edge[0] + edge[1] + edge[2] + edge[3]
    if summatory > 0:
        raise Exception(
            "Points are not clockwise. The coordinates of bounding quadrilaterals have to be given in clockwise order. Regarding the correct interpretation of 'clockwise' remember that the image coordinate system used is the standard one, with the image origin at the upper left, the X axis extending to the right and Y axis extending downwards."
        )


def get_tl_line_values_from_file_contents(
    content,
    CRLF=True,
    LTRB=True,
    withTranscription=False,
    withConfidence=False,
    imWidth=0,
    imHeight=0,
    sort_by_confidences=True,
):
    """
    Returns all points, confindences and transcriptions of a file in lists. Valid line formats:
    xmin,ymin,xmax,ymax,[confidence],[transcription]
    x1,y1,x2,y2,x3,y3,x4,y4,[confidence],[transcription]
    """
    pointsList = []
    transcriptionsList = []
    confidencesList = []

    lines = content.split("\r\n" if CRLF else "\n")
    for line in lines:
        line = line.replace("\r", "").replace("\n", "")
        if line != "":
            points, confidence, transcription = get_tl_line_values(
                line, LTRB, withTranscription, withConfidence, imWidth, imHeight
            )
            pointsList.append(points)
            transcriptionsList.append(transcription)
            confidencesList.append(confidence)

    if withConfidence and len(confidencesList) > 0 and sort_by_confidences:
        import numpy as np

        sorted_ind = np.argsort(-np.array(confidencesList))
        confidencesList = [confidencesList[i] for i in sorted_ind]
        pointsList = [pointsList[i] for i in sorted_ind]
        transcriptionsList = [transcriptionsList[i] for i in sorted_ind]

    return pointsList, confidencesList, transcriptionsList


def main_evaluation(
    p,
    default_evaluation_params_fn,
    validate_data_fn,
    evaluate_method_fn,
    show_result=True,
    per_sample=True,
):
    """
    This process validates a method, evaluates it and if it succeed generates a ZIP file with a JSON entry for each sample.
    Params:
    p: Dictionary of parameters with the GT/submission locations. If None is passed, the parameters send by the system are used.
    default_evaluation_params_fn: points to a function that returns a dictionary with the default parameters used for the evaluation
    validate_data_fn: points to a method that validates the correct format of the submission
    evaluate_method_fn: points to a function that evaluated the submission and return a Dictionary with the results
    """
    evalParams = default_evaluation_params_fn()
    if "p" in p.keys():
        evalParams.update(
            p["p"] if isinstance(p["p"], dict) else json.loads(p["p"][1:-1])
        )

    resDict = {"calculated": True, "Message": "", "method": "{}", "per_sample": "{}"}
    try:
        # validate_data_fn(p['g'], p['s'], evalParams)
        evalData = evaluate_method_fn(p["g"], p["s"], evalParams)
        resDict.update(evalData)

    except Exception as e:
        traceback.print_exc()
        resDict["Message"] = str(e)
        resDict["calculated"] = False

    if "o" in p:
        if not os.path.exists(p["o"]):
            os.makedirs(p["o"])

        resultsOutputname = p["o"] + "/results.zip"
        outZip = zipfile.ZipFile(resultsOutputname, mode="w", allowZip64=True)

        del resDict["per_sample"]
        if "output_items" in resDict.keys():
            del resDict["output_items"]

        outZip.writestr("method.json", json.dumps(resDict))

    if not resDict["calculated"]:
        if show_result:
            sys.stderr.write("Error!\n" + resDict["Message"] + "\n\n")
        if "o" in p:
            outZip.close()
        return resDict

    if "o" in p:
        if per_sample == True:
            for k, v in evalData["per_sample"].iteritems():
                outZip.writestr(k + ".json", json.dumps(v))

            if "output_items" in evalData.keys():
                for k, v in evalData["output_items"].iteritems():
                    outZip.writestr(k, v)

        outZip.close()

    if show_result:
        sys.stdout.write("Calculated!")
        sys.stdout.write(json.dumps(resDict["method"]))

    return resDict


def main_validation(default_evaluation_params_fn, validate_data_fn):
    """
    This process validates a method
    Params:
    default_evaluation_params_fn: points to a function that returns a dictionary with the default parameters used for the evaluation
    validate_data_fn: points to a method that validates the correct format of the submission
    """
    try:
        p = dict([s[1:].split("=") for s in sys.argv[1:]])
        evalParams = default_evaluation_params_fn()
        if "p" in p.keys():
            evalParams.update(
                p["p"] if isinstance(p["p"], dict) else json.loads(p["p"][1:-1])
            )

        validate_data_fn(p["g"], p["s"], evalParams)
        print("SUCCESS")
        sys.exit(0)
    except Exception as e:
        print(str(e))
        sys.exit(101)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     Global:
  model_name: PP-OCRv4_mobile_det # To use static model for inference.
  debug: false
  use_gpu: true
  epoch_num: &epoch_num 500
  log_smooth_window: 20
  print_batch_step: 100
  save_model_dir: ./output/PP-OCRv4_mobile_det
  save_epoch_step: 10
  eval_batch_step:
  - 0
  - 1500
  cal_metric_during_train: false
  checkpoints:
  pretrained_model: https://paddleocr.bj.bcebos.com/pretrained/PPLCNetV3_x0_75_ocr_det.pdparams
  save_inference_dir: null
  use_visualdl: false
  infer_img: doc/imgs_en/img_10.jpg
  save_res_path: ./checkpoints/det_db/predicts_db.txt
  d2s_train_image_shape: [3, 640, 640]
  distributed: true

Architecture:
  model_type: det
  algorithm: DB
  Transform: null
  Backbone:
    name: PPLCNetV3
    scale: 0.75
    det: True
  Neck:
    name: RSEFPN
    out_channels: 96
    shortcut: True
  Head:
    name: DBHead
    k: 50
    fix_nan: True

Loss:
  name: DBLoss
  balance_loss: true
  main_loss_type: DiceLoss
  alpha: 5
  beta: 10
  ohem_ratio: 3

Optimizer:
  name: Adam
  beta1: 0.9
  beta2: 0.999
  lr:
    name: Cosine
    learning_rate: 0.001 #(8*8c)
    warmup_epoch: 2
  regularizer:
    name: L2
    factor: 5.0e-05

PostProcess:
  name: DBPostProcess
  thresh: 0.3
  box_thresh: 0.6
  max_candidates: 1000
  unclip_ratio: 1.5

Metric:
  name: DetMetric
  main_indicator: hmean

Train:
  dataset:
    name: SimpleDataSet
    data_dir: ./train_data/icdar2015/text_localization/
    label_file_list:
      - ./train_data/icdar2015/text_localization/train_icdar2015_label.txt
    ratio_list: [1.0]
    transforms:
    - DecodeImage:
        img_mode: BGR
        channel_first: false
    - DetLabelEncode: null
    - CopyPaste: null
    - IaaAugment:
        augmenter_args:
        - type: Fliplr
          args:
            p: 0.5
        - type: Affine
          args:
            rotate:
            - -10
            - 10
        - type: Resize
          args:
            size:
            - 0.5
            - 3
    - EastRandomCropData:
        size:
        - 640
        - 640
        max_tries: 50
        keep_ratio: true
    - MakeBorderMap:
        shrink_ratio: 0.4
        thresh_min: 0.3
        thresh_max: 0.7
        total_epoch: *epoch_num
    - MakeShrinkMap:
        shrink_ratio: 0.4
        min_text_size: 8
        total_epoch: *epoch_num
    - NormalizeImage:
        scale: 1./255.
        mean:
        - 0.485
        - 0.456
        - 0.406
        std:
        - 0.229
        - 0.224
        - 0.225
        order: hwc
    - ToCHWImage: null
    - KeepKeys:
        keep_keys:
        - image
        - threshold_map
        - threshold_mask
        - shrink_map
        - shrink_mask
  loader:
    shuffle: true
    drop_last: false
    batch_size_per_card: 8
    num_workers: 8

Eval:
  dataset:
    name: SimpleDataSet
    data_dir: ./train_data/icdar2015/text_localization/
    label_file_list:
      - ./train_data/icdar2015/text_localization/test_icdar2015_label.txt
    transforms:
    - DecodeImage:
        img_mode: BGR
        channel_first: false
    - DetLabelEncode: null
    - DetResizeForTest:
    - NormalizeImage:
        scale: 1./255.
        mean:
        - 0.485
        - 0.456
        - 0.406
        std:
        - 0.229
        - 0.224
        - 0.225
        order: hwc
    - ToCHWImage: null
    - KeepKeys:
        keep_keys:
        - image
        - shape
        - polys
        - ignore_tags
  loader:
    shuffle: false
    drop_last: false
    batch_size_per_card: 1
    num_workers: 2
profiler_options: null
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                #!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import namedtuple
import numpy as np
from shapely.geometry import Polygon
import cv2


def iou_rotate(box_a, box_b, method="union"):
    rect_a = cv2.minAreaRect(box_a)
    rect_b = cv2.minAreaRect(box_b)
    r1 = cv2.rotatedRectangleIntersection(rect_a, rect_b)
    if r1[0] == 0:
        return 0
    else:
        inter_area = cv2.contourArea(r1[1])
        area_a = cv2.contourArea(box_a)
        area_b = cv2.contourArea(box_b)
        union_area = area_a + area_b - inter_area
        if union_area == 0 or inter_area == 0:
            return 0
        if method == "union":
            iou = inter_area / union_area
        elif method == "intersection":
            iou = inter_area / min(area_a, area_b)
        else:
            raise NotImplementedError
        return iou


class DetectionIoUEvaluator(object):
    def __init__(
        self, is_output_polygon=False, iou_constraint=0.5, area_precision_constraint=0.5
    ):
        self.is_output_polygon = is_output_polygon
        self.iou_constraint = iou_constraint
        self.area_precision_constraint = area_precision_constraint

    def evaluate_image(self, gt, pred):
        def get_union(pD, pG):
            return Polygon(pD).union(Polygon(pG)).area

        def get_intersection_over_union(pD, pG):
            return get_intersection(pD, pG) / get_union(pD, pG)

        def get_intersection(pD, pG):
            return Polygon(pD).intersection(Polygon(pG)).area

        def compute_ap(confList, matchList, numGtCare):
            correct = 0
            AP = 0
            if len(confList) > 0:
                confList = np.array(confList)
                matchList = np.array(matchList)
                sorted_ind = np.argsort(-confList)
                confList = confList[sorted_ind]
                matchList = matchList[sorted_ind]
                for n in range(len(confList)):
                    match = matchList[n]
                    if match:
                        correct += 1
                        AP += float(correct) / (n + 1)

                if numGtCare > 0:
                    AP /= numGtCare

            return AP

        perSampleMetrics = {}

        matchedSum = 0

        Rectangle = namedtuple("Rectangle", "xmin ymin xmax ymax")

        numGlobalCareGt = 0
        numGlobalCareDet = 0

        arrGlobalConfidences = []
        arrGlobalMatches = []

        recall = 0
        precision = 0
        hmean = 0

        detMatched = 0

        iouMat = np.empty([1, 1])

        gtPols = []
        detPols = []

        gtPolPoints = []
        detPolPoints = []

        # Array of Ground Truth Polygons' keys marked as don't Care
        gtDontCarePolsNum = []
        # Array of Detected Polygons' matched with a don't Care GT
        detDontCarePolsNum = []

        pairs = []
        detMatchedNums = []

        arrSampleConfidences = []
        arrSampleMatch = []

        evaluationLog = ""

        for n in range(len(gt)):
            points = gt[n]["points"]
            # transcription = gt[n]['text']
            dontCare = gt[n]["ignore"]

            if not Polygon(points).is_valid or not Polygon(points).is_simple:
                continue

            gtPol = points
            gtPols.append(gtPol)
            gtPolPoints.append(points)
            if dontCare:
                gtDontCarePolsNum.append(len(gtPols) - 1)

        evaluationLog += (
            "GT polygons: "
            + str(len(gtPols))
            + (
                " (" + str(len(gtDontCarePolsNum)) + " don't care)\n"
                if len(gtDontCarePolsNum) > 0
                else "\n"
            )
        )

        for n in range(len(pred)):
            points = pred[n]["points"]
            if not Polygon(points).is_valid or not Polygon(points).is_simple:
                continue

            detPol = points
            detPols.append(detPol)
            detPolPoints.append(points)
            if len(gtDontCarePolsNum) > 0:
                for dontCarePol in gtDontCarePolsNum:
                    dontCarePol = gtPols[dontCarePol]
                    intersected_area = get_intersection(dontCarePol, detPol)
                    pdDimensions = Polygon(detPol).area
                    precision = (
                        0 if pdDimensions == 0 else intersected_area / pdDimensions
                    )
                    if precision > self.area_precision_constraint:
                        detDontCarePolsNum.append(len(detPols) - 1)
                        break

        evaluationLog += (
            "DET polygons: "
            + str(len(detPols))
            + (
                " (" + str(len(detDontCarePolsNum)) + " don't care)\n"
                if len(detDontCarePolsNum) > 0
                else "\n"
            )
        )

        if len(gtPols) > 0 and len(detPols) > 0:
            # Calculate IoU and precision matrixs
            outputShape = [len(gtPols), len(detPols)]
            iouMat = np.empty(outputShape)
            gtRectMat = np.zeros(len(gtPols), np.int8)
            detRectMat = np.zeros(len(detPols), np.int8)
            if self.is_output_polygon:
                for gtNum in range(len(gtPols)):
                    for detNum in range(len(detPols)):
                        pG = gtPols[gtNum]
                        pD = detPols[detNum]
                        iouMat[gtNum, detNum] = get_intersection_over_union(pD, pG)
            else:
                # gtPols = np.float32(gtPols)
                # detPols = np.float32(detPols)
                for gtNum in range(len(gtPols)):
                    for detNum in range(len(detPols)):
                        pG = np.float32(gtPols[gtNum])
                        pD = np.float32(detPols[detNum])
                        iouMat[gtNum, detNum] = iou_rotate(pD, pG)
            for gtNum in range(len(gtPols)):
                for detNum in range(len(detPols)):
                    if (
                        gtRectMat[gtNum] == 0
                        and detRectMat[detNum] == 0
                        and gtNum not in gtDontCarePolsNum
                        and detNum not in detDontCarePolsNum
                    ):
                        if iouMat[gtNum, detNum] > self.iou_constraint:
                            gtRectMat[gtNum] = 1
                            detRectMat[detNum] = 1
                            detMatched += 1
                            pairs.append({"gt": gtNum, "det": detNum})
                            detMatchedNums.append(detNum)
                            evaluationLog += (
                                "Match GT #"
                                + str(gtNum)
                                + " with Det #"
                                + str(detNum)
                                + "\n"
                            )

        numGtCare = len(gtPols) - len(gtDontCarePolsNum)
        numDetCare = len(detPols) - len(detDontCarePolsNum)
        if numGtCare == 0:
            recall = float(1)
            precision = float(0) if numDetCare > 0 else float(1)
        else:
            recall = float(detMatched) / numGtCare
            precision = 0 if numDetCare == 0 else float(detMatched) / numDetCare

        hmean = (
            0
            if (precision + recall) == 0
            else 2.0 * precision * recall / (precision + recall)
        )

        matchedSum += detMatched
        numGlobalCareGt += numGtCare
        numGlobalCareDet += numDetCare

        perSampleMetrics = {
            "precision": precision,
            "recall": recall,
            "hmean": hmean,
            "pairs": pairs,
            "iouMat": [] if len(detPols) > 100 else iouMat.tolist(),
            "gtPolPoints": gtPolPoints,
            "detPolPoints": detPolPoints,
            "gtCare": numGtCare,
            "detCare": numDetCare,
            "gtDontCare": gtDontCarePolsNum,
            "detDontCare": detDontCarePolsNum,
            "detMatched": detMatched,
            "evaluationLog": evaluationLog,
        }

        return perSampleMetrics

    def combine_results(self, results):
        numGlobalCareGt = 0
        numGlobalCareDet = 0
        matchedSum = 0
        for result in results:
            numGlobalCareGt += result["gtCare"]
            numGlobalCareDet += result["detCare"]
            matchedSum += result["detMatched"]

        methodRecall = (
            0 if numGlobalCareGt == 0 else float(matchedSum) / numGlobalCareGt
        )
        methodPrecision = (
            0 if numGlobalCareDet == 0 else float(matchedSum) / numGlobalCareDet
        )
        methodHmean = (
            0
            if methodRecall + methodPrecision == 0
            else 2 * methodRecall * methodPrecision / (methodRecall + methodPrecision)
        )

        methodMetrics = {
            "precision": methodPrecision,
            "recall": methodRecall,
            "hmean": methodHmean,
        }

        return methodMetrics


if __name__ == "__main__":
    evaluator = DetectionIoUEvaluator()
    preds = [
        [
            {
                "points": [(0.1, 0.1), (0.5, 0), (0.5, 1), (0, 1)],
                "text": 1234,
                "ignore": False,
            },
            {
                "points": [(0.5, 0.1), (1, 0), (1, 1), (0.5, 1)],
                "text": 5678,
                "ignore": False,
            },
        ]
    ]
    gts = [
        [
            {
                "points": [(0.1, 0.1), (1, 0), (1, 1), (0, 1)],
                "text": 123,
                "ignore": False,
            }
        ]
    ]
    results = []
    for gt, pred in zip(gts, preds):
        results.append(evaluator.evaluate_image(gt, pred))
    metrics = evaluator.combine_results(results)
    print(metrics)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              