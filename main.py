import argparse;
import math;
import random;
import pygame;
import copy;

from enum import Enum, auto;

################################################################################

class Interpolation(Enum):
  LINEAR = auto()
  COSINE = auto()

class Noise1D:
  _size  = 0;
  _noise = [];
  _amplitude = 1.0;
  _seed = None;

  # ----------------------------------------------------------------------------

  def __init__(self, size : int, amplitude : float = 1.0, seed = None):
    self._size = size;

    self.Reset(size, amplitude, seed);

  # ----------------------------------------------------------------------------

  def Reset(self, newSize : int = 0, newAmp : float = 1.0, newSeed = None):
    if (newSize > 0):
      self._size = newSize;

    self._amplitude = newAmp;
    self._noise     = [ 0 ] * newSize;
    self._seed      = newSeed;

    random.seed(self._seed);

    for i in range(self._size):
      self._noise[i] = random.random() * self._amplitude;

  # ----------------------------------------------------------------------------

  def Noise(self, x : float, interpolation=Interpolation.COSINE):
    ind = int(x);

    t = math.modf(x)[0];

    y1 = self._noise[ind       % self._size];
    y2 = self._noise[(ind + 1) % self._size];

    if interpolation is Interpolation.LINEAR:
      val = (1 - t) * y1 + t * y2;
    else:
      val = (math.cos(t * math.pi) + 1) * 0.5 * (y1 - y2) + y2;

    return val;

  # ----------------------------------------------------------------------------

  def PrintNoise(self):
    for item in self._noise:
      print(f"{item:.4f}, ", end="");

    print();

################################################################################

def DrawBorder(screen,
               borders : pygame.Surface,
               index : int,
               pos : tuple,
               scale : int,
               tileSize : int):
  ind = index % 16;
  x = ind * tileSize * scale;
  screen.blit(borders, pos, (x, 0, tileSize * scale, tileSize * scale));

################################################################################

def CellToInd(grid, x, y) -> int:

  zero  = grid[x][y];
  one   = grid[x][y + 1];
  two   = grid[x + 1][y + 1];
  three = grid[x + 1][y];

  binaryNumber = int(f"{ three }{ two }{ one }{ zero }", 2);

  return binaryNumber;

################################################################################

def DrawLines(screen, screenRes : list, cellSize):
  clr = (32, 32, 32);

  for x in range(0, screenRes[0], cellSize):
    pygame.draw.line(screen, clr, (x, 0), (x, screenRes[1]), 1);

  for y in range(0, screenRes[1], cellSize):
    pygame.draw.line(screen, clr, (0, y), (screenRes[0], y), 1);

################################################################################

def SetColor(img : pygame.Surface, color : pygame.Color) -> pygame.Surface:
  imageClr = pygame.Surface(img.get_size());
  imageClr.fill(color);

  finalImage = img.copy();
  finalImage.blit(imageClr, (0, 0), special_flags=pygame.BLEND_MULT);

  return finalImage;

################################################################################

def CreateGrid(screenSize : list,
               cellSize : int,
               threshold : float,
               noiseStep : float,
               resolution : int) -> list:
  grid = [];

  noiseInd = 0.0;

  pn = Noise1D(resolution);

  for y in range(0, screenSize[1] + cellSize, cellSize):
    line = [];
    for x in range(0, screenSize[0] + cellSize, cellSize):
      noiseVal = 0;

      if (y == 0 or x == 0 or x >= screenSize[0] or y >= screenSize[1]):
        noiseVal = 0;
      else:
        noiseVal = pn.Noise(noiseInd);
        noiseVal = 0 if noiseVal < threshold else 1;

      line.append(noiseVal);
      noiseInd += noiseStep;

    grid.append(line);

  return grid;

################################################################################

def Print(screen, font, text, pos : tuple, color : tuple):
  ts, _ = font.render(text, color);
  screen.blit(ts, pos);

################################################################################

def ExtractChunk(grid, x, y) -> int:
  chunk = 0;

  bytePos = 0;

  for i in range(-1, 2, 1):
    for j in range(-1, 2, 1):
      num = grid[x + i][y + j];
      chunk |= (num << bytePos);
      bytePos += 1;

  return chunk;

################################################################################

def IsBad(chunk : int) -> bool:
  '''
  ...
  .#. -> 000010000
  ...

  #..
  .#. -> 000010001
  ...

  ..#
  .#. -> 000010100
  ...

  ...
  .#. -> 100010000
  ..#

  ...
  .#. -> 001010000
  #..

  #.#
  .#. -> 000010101
  ...

  ..#
  .#. -> 100010100
  ..#

  ...
  .#. -> 101010000
  #.#

  #..
  .#. -> 001010001
  #..

  #..
  .#. -> 100010001
  ..#

  ..#
  .#. -> 001010100
  #..

  #.#
  .#. -> 100010101
  ..#

  ..#
  .#. -> 101010100
  #.#

  #.#
  .#. -> 001010101
  #..

  #.#
  .#. -> 101010101
  #.#
  '''

  badChunks = [
    0b000010000,
    0b000010001,
    0b000010100,
    0b100010000,
    0b001010000,
    0b000010101,
    0b100010100,
    0b101010000,
    0b001010001,
    0b100010001,
    0b001010100,
    0b100010101,
    0b101010100,
    0b001010101,
    0b101010101
  ];

  return chunk in badChunks;

################################################################################

def CountAround(grid, x, y) -> int:
  pts = 0;

  for i in range(-1, 2, 1):
    for j in range(-1, 2, 1):
      num = grid[x + i][y + j];
      if num == 1:
        pts += 1;

  return pts;

################################################################################

def PostProcess(grid, dimX, dimY) -> list:
  offsets = [
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1)
  ];

  ppGrid = copy.deepcopy(grid);

  # Remove single points

  for y in range(1, dimY - 2, 1):
    for x in range(1, dimX - 2, 1):
      chunk = ExtractChunk(ppGrid, x, y);

      if IsBad(chunk):
        ppGrid[x][y] = 0;

  # Merge small chunks into bigger chunks

  for y in range(1, dimY - 2, 1):
    for x in range(1, dimX - 2, 1):
      pts = CountAround(ppGrid, x, y);

      if pts >= 5:
        ppGrid[x][y] = 1;

  return ppGrid;

################################################################################

def main():
  parser = argparse.ArgumentParser();

  parser.add_argument("--scale",     help="Scale factor. Default: 3");
  parser.add_argument("--step",      help="Noise step. Default: 1.0");
  parser.add_argument("--threshold", help="Points threshold. Default: 0.5");
  parser.add_argument("--period",    help="Noise period. Default: (window.w * window.h) // cellSize");

  args = parser.parse_args();

  sx = 1280;
  sy = 720;

  screenSize = [ sx, sy ];

  scaleFactor = 3;
  noiseStep   = 1.0;
  threshold   = 0.5;

  try:
    if args.scale is not None:
      scaleFactor = int(args.scale);

    if args.step is not None:
      noiseStep = float(args.step);

    if args.threshold is not None:
      threshold = float(args.threshold);

  except:
    print("Numbers only!");
    exit(1);

  if scaleFactor <= 0 or noiseStep < 0.0 or threshold < 0.0:
    print("Values must be positive!");
    exit(1);

  pygame.init();

  pygame.display.set_caption("Marching squares test");

  screen = pygame.display.set_mode(screenSize);
  font   = pygame.freetype.Font(None, 16);

  c = pygame.time.Clock();

  running = True;

  bordersList = [
    pygame.image.load("borders/borders.png"),
    pygame.image.load("borders/borders-filled.png"),
    pygame.image.load("borders/borders-rounded.png"),
    pygame.image.load("borders/borders-rounded-filled.png"),
    pygame.image.load("borders/borders-square.png"),
    pygame.image.load("borders/borders-square-inv.png")
  ];

  imgRect = bordersList[0].get_size();

  tilesetDim = (imgRect[0], imgRect[1]);

  bordersScaled = [];

  for item in bordersList:
    imgRect = item.get_size();
    border = pygame.transform.scale(item,
                                   (
                                     imgRect[0] * scaleFactor,
                                     imgRect[1] * scaleFactor
                                   ));
    bordersScaled.append(border);

  tileSize = (tilesetDim[0] // 16);
  cellSize = tileSize * scaleFactor;

  resolution = (sx * sy) // cellSize;

  try:
    if args.period is not None:
      resolution = int(args.period);
  except:
    print("Numbers only!");
    exit(1);

  if resolution <= 0:
    print("Noise period must be greater than zero!");
    exit(1);

  grid = CreateGrid(screenSize,
                    cellSize,
                    threshold,
                    noiseStep,
                    resolution);

  dimX = len(grid);
  dimY = len(grid[0]);

  print(f"{ dimX }x{ dimY }");

  ppGrid = PostProcess(grid, dimX, dimY);

  ppFlag = False;

  currentGrid = grid;

  pointColor = (0, 255, 255);
  blackColor = (0, 0, 0);
  fontColor  = (255, 255, 255);

  borderColor = pygame.Color(64, 64, 64);

  pointSize = scaleFactor / 2;

  pointSize = 1.0 if pointSize < 1.0 else pointSize;

  tilesetInd = 0;

  hideText   = False;
  showPoints = False;

  while running:

    c.tick(60);

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False;
      elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          running = False;
        elif event.key == pygame.K_SPACE:
          grid   = CreateGrid(screenSize,
                              cellSize,
                              threshold,
                              noiseStep,
                              resolution);
          ppGrid = PostProcess(grid, dimX, dimY);
          currentGrid = grid if not ppFlag else ppGrid;
        elif event.key == pygame.K_LEFT:
          tilesetInd += -1;
          tilesetInd = tilesetInd % len(bordersList);
        elif event.key == pygame.K_RIGHT:
          tilesetInd += 1;
          tilesetInd = tilesetInd % len(bordersList);
        elif event.key == pygame.K_h:
          hideText = not hideText;
        elif event.key == pygame.K_s:
          showPoints = not showPoints;
        elif event.key == pygame.K_p:
          ppFlag = not ppFlag;
          currentGrid = grid if not ppFlag else ppGrid;

    screen.fill(blackColor);

    DrawLines(screen, screenSize, cellSize);

    surf = SetColor(bordersScaled[tilesetInd], borderColor);

    for y in range(dimY - 1):
      for x in range(dimX - 1):
        borderInd = CellToInd(currentGrid, x, y);
        DrawBorder(screen,
                   surf,
                   borderInd,
                   (
                     y * tileSize * scaleFactor,
                     x * tileSize * scaleFactor
                   ),
                   scaleFactor,
                   tileSize);

        if showPoints and currentGrid[x][y] == 1:
          pygame.draw.circle(screen,
                             pointColor,
                             (
                               y * tileSize * scaleFactor,
                               x * tileSize * scaleFactor
                             ),
                             pointSize);

    if not hideText:
      Print(screen,
            font,
            (
              f"scaleFactor = { scaleFactor }, "
              f"noiseStep = { noiseStep }, "
              f"threshold = { threshold }, "
              f"period = { resolution }, "
              f"tileset = { tilesetInd }, "
              f"preprocessing = { ppFlag }"
            ),
            (0, 0),
            fontColor);

      Print(screen,
            font,
            "Press 'Space' to regenerate grid",
            (screenSize[0] - 250, 0),
            fontColor);

      Print(screen,
            font,
            "Use 'Left' or 'Right' to switch between tilesets",
            (screenSize[0] - 350, 32),
            fontColor);

      Print(screen,
            font,
            "Press 'S' to show points",
            (screenSize[0] - 190, 64),
            fontColor);

      Print(screen,
            font,
            "Press 'H' to hide text",
            (screenSize[0] - 170, 96),
            fontColor);

      Print(screen,
            font,
            "Press 'P' to toggle preprocess",
            (screenSize[0] - 240, 128),
            fontColor);

    pygame.display.flip();

  pygame.quit();

################################################################################

if __name__ == "__main__":
  main();
