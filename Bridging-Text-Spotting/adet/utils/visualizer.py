import numpy as np
import pickle
from detectron2.utils.visualizer import Visualizer
import matplotlib.colors as mplc
import matplotlib.font_manager as mfm
import matplotlib as mpl
import matplotlib.figure as mplfigure
import random
import string
import cv2

class TextVisualizer(Visualizer):
    def __init__(self, image, metadata, instance_mode, cfg):
        Visualizer.__init__(self, image, metadata, instance_mode=instance_mode)
        self.voc_size = cfg.MODEL.BATEXT.VOC_SIZE
        self.use_customer_dictionary = cfg.MODEL.BATEXT.CUSTOM_DICT
        self.use_polygon = cfg.MODEL.TRANSFORMER.USE_POLYGON
        self.use_bbox = cfg.MODEL.TRANSFORMER.USE_BOX
        if not self.use_customer_dictionary:
            self.CTLABELS = [' ','!','"','#','$','%','&','\'','(',')','*','+',',','-','.','/',
                             '0','1','2','3','4','5','6','7','8','9',':',';','<','=','>','?','@',
                             'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q',
                             'R','S','T','U','V','W','X','Y','Z','[','\\',']','^','_','`','a','b',
                             'c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s',
                             't','u','v','w','x','y','z','{','|','}','~']
        else:
            with open(self.use_customer_dictionary, 'rb') as fp:
                self.CTLABELS = pickle.load(fp)
        assert(int(self.voc_size - 1) == len(self.CTLABELS)), "voc_size is not matched dictionary size, got {} and {}.".format(int(self.voc_size - 1), len(self.CTLABELS))
        self.voc = list(string.printable[:-6])
        
    def draw_instance_predictions(self, predictions):
        if self.use_polygon:
            ctrl_pnts = predictions.polygons.numpy()
        else:
            ctrl_pnts = predictions.beziers.numpy()
        scores = predictions.scores.tolist()
        recs = predictions.recs
        if self.use_bbox:
            bboxes = predictions.boxes.numpy()

            self.overlay_bboxes(bboxes, scores, recs)

        else:
            print("use polygon")
            self.overlay_instances(ctrl_pnts, scores, recs)

        return self.output
    # def draw_instance_predictions(self, predictions):
    #     scores = predictions.scores.tolist()
    #     recs = predictions.recs
        
    #     if self.use_bbox:
    #         # Only load bboxes if we're using them
    #         bboxes = predictions.boxes.numpy()
    #         self.overlay_bboxes(bboxes, scores, recs)
    #     else:
    #         # Only load polygon/bezier data if we're using them
    #         if self.use_polygon:
    #             ctrl_pnts = predictions.polygons.numpy()
    #         else:
    #             ctrl_pnts = predictions.beziers.numpy()
    #         self.overlay_instances(ctrl_pnts, scores, recs)

    #     return self.output
    
    def overlay_bboxes(self, bboxes, scores, recs, alpha=0.4):
        colors = [(0,0,1), (0,1,0), (1,0,0), (1,1,0), (1,0,1), (0,1,1)]
        for bbox, score, rec in zip(bboxes, scores, recs):
                color = random.choice(colors)
                rec_string = self.rec_decode(rec)
                self.draw_box(bbox, edge_color=color, alpha=alpha)
                text = "score: {:.2f}".format(score)
                # self.draw_text(rec_string, polygon[0], horizontal_alignment="left")
                # self.draw_text(f"{rec_string}\n{text}", bbox[:2], horizontal_alignment="left")
                # you can also visualize the predicted point drift between decoder layers.

    def _ctrl_pnt_to_poly(self, pnt):
        if self.use_polygon:
            points = pnt.reshape(-1, 2)
        else:
            # bezier to polygon
            u = np.linspace(0, 1, 20)
            pnt = pnt.reshape(2, 4, 2).transpose(0, 2, 1).reshape(4, 4)
            points = np.outer((1 - u) ** 3, pnt[:, 0]) \
                + np.outer(3 * u * ((1 - u) ** 2), pnt[:, 1]) \
                + np.outer(3 * (u ** 2) * (1 - u), pnt[:, 2]) \
                + np.outer(u ** 3, pnt[:, 3])
            points = np.concatenate((points[:, :2], points[:, 2:]), axis=0)

        return points

    def rec_decode(self, rec):
        s = ''
        for c in rec:
            c = int(c)
            if c < len(self.voc):
                s += self.voc[c]
            elif c == len(self.voc):
                return s
            else:
                s += u''
        return s

    def _decode_recognition(self, rec):
        s = ''
        for c in rec:
            c = int(c)
            if c < self.voc_size - 1:
                if self.voc_size == 96:
                    s += self.CTLABELS[c]
                else:
                    s += str(chr(self.CTLABELS[c]))
            elif c == self.voc_size -1:
                s += u'口'
        return s

    def _ctc_decode_recognition(self, rec):
        # ctc decoding
        last_char = False
        s = ''
        for c in rec:
            c = int(c)
            if c < self.voc_size - 1:
                if last_char != c:
                    if self.voc_size == 96:
                        s += self.CTLABELS[c]
                        last_char = c
                    else:
                        s += str(chr(self.CTLABELS[c]))
                        last_char = c
            elif c == self.voc_size -1:
                s += u'口'
            else:
                last_char = False
        return s

    def overlay_instances(self, ctrl_pnts, scores, recs, alpha=0.4):
        colors = [(0,0,1), (0,1,0), (1,0,0), (1,1,0), (1,0,1), (0,1,1)]
        for ctrl_pnt, score, rec in zip(ctrl_pnts, scores, recs):
                polygon = self._ctrl_pnt_to_poly(ctrl_pnt)
                color = random.choice(colors)
                rec_string = self.rec_decode(rec)
                self.draw_polygon(polygon, color, alpha=alpha)
                self.draw_circle(polygon[0], 'w', radius=3)  # vis the start point
                self.draw_circle(polygon[0], 'g', radius=2)
                text = "score: {:.2f}".format(score)
                # self.draw_text(rec_string, polygon[0], horizontal_alignment="left")
                self.draw_text(f"{rec_string}\n{text}", polygon[0], horizontal_alignment="left")
                # you can also visualize the predicted point drift between decoder layers.

    def draw_text(
        self,
        text,
        position,
        *,
        font_size=None,
        color="g",
        horizontal_alignment="center",
        rotation=0,
        draw_chinese=False
    ):
        """
        Args:
            text (str): class label
            position (tuple): a tuple of the x and y coordinates to place text on image.
            font_size (int, optional): font of the text. If not provided, a font size
                proportional to the image width is calculated and used.
            color: color of the text. Refer to `matplotlib.colors` for full list
                of formats that are accepted.
            horizontal_alignment (str): see `matplotlib.text.Text`
            rotation: rotation angle in degrees CCW
        Returns:
            output (VisImage): image object with text drawn.
        """
        if not font_size:
            font_size = self._default_font_size

        # since the text background is dark, we don't want the text to be dark
        color = np.maximum(list(mplc.to_rgb(color)), 0.2)
        color[np.argmax(color)] = max(0.8, np.max(color))
        
        x, y = position
        if draw_chinese:
            font_path = "./simsun.ttc"
            prop = mfm.FontProperties(fname=font_path)
            self.output.ax.text(
                x,
                y,
                text,
                size=font_size * self.output.scale,
                family="sans-serif",
                bbox={"facecolor": "black", "alpha": 0.0, "pad": 0.7, "edgecolor": "none"},
                verticalalignment="top",
                horizontalalignment=horizontal_alignment,
                color=color,
                zorder=10,
                rotation=rotation,
                fontproperties=prop
            )
        else:
            self.output.ax.text(
                x,
                y,
                text,
                size=font_size * self.output.scale,
                family="sans-serif",
                bbox={"facecolor": "black", "alpha": 0.5, "pad": 0.7, "edgecolor": "none"},
                verticalalignment="top",
                horizontalalignment=horizontal_alignment,
                color=color,
                zorder=10,
                rotation=rotation,
            )
        return self.output
