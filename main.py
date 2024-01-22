#!/opt/rh/rh-python38/root/usr/bin/python3

import math;
import random;
import pygame;

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

def DrawBorder(screen, borders : pygame.Surface, index : int, pos : tuple, scale : int):
  ind = index % 16;
  x = ind * 9 * scale;
  screen.blit(borders, pos, (x, 0, 9 * scale, 9 * scale));

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

def main():
  sx = 1280;
  sy = 720;

  screenSize = [ sx, sy ];

  scaleFactor = 3;

  pygame.init();

  pygame.display.set_caption("Marching squared test");

  screen = pygame.display.set_mode(screenSize);

  c = pygame.time.Clock();

  running = True;

  noiseStep = 1;

  cellSize = 9 * scaleFactor;

  resolution = (screenSize[0] * screenSize[1]) // cellSize;
  pn = Noise1D(resolution);

  borders = pygame.image.load("borders-filled.png");
  #borders = pygame.image.load("borders.png");
  borders = pygame.transform.scale(borders, (144 * scaleFactor, 9 * scaleFactor));

  grid = [];

  noiseInd = 0.0;

  threshold = 0.5;

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

  dimX = len(grid);
  dimY = len(grid[0]);

  print(f"{ dimX }x{ dimY }");

  pointColor = (255, 255, 255);
  blackColor = (0, 0, 0);

  borderColor = pygame.Color(64, 64, 64);

  while running:

    c.tick(60);

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False;
      elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          running = False;

    screen.fill(blackColor);

    DrawLines(screen, screenSize, cellSize);

    surf = SetColor(borders, borderColor);

    for y in range(dimY - 1):
      for x in range(dimX - 1):
        borderInd = CellToInd(grid, x, y);
        clr = pointColor if grid[x][y] == 1 else blackColor;
        DrawBorder(screen,
                   surf,
                   borderInd,
                   (y * 9 * scaleFactor, x * 9 * scaleFactor),
                   scaleFactor);
        pygame.draw.circle(screen, clr, (y * 9 * scaleFactor, x * 9 * scaleFactor), 1);

    pygame.display.flip();

  pygame.quit();

################################################################################

if __name__ == "__main__":
  main();
