package main

import (
	"image/color"

	"github.com/hajimehoshi/ebiten"
	"github.com/hajimehoshi/ebiten/ebitenutil"
)

const (
	ScreenWidth  = 640
	ScreenHeight = 480
)

type MoveDir int

const (
	MoveNone MoveDir = iota
	MoveUp
	MoveLeft
	MoveDown
	MoveRight
)

type Position struct {
	x int
	y int
}
type Game struct {
	Current   Position
	Speed     int
	MoveDir   MoveDir
	CountDown int
}

func NewGame() Game {
	return Game{
		Speed: 2,
	}
}

func (g Game) Update(screen *ebiten.Image) error {

	if ebiten.IsKeyPressed(ebiten.KeyUp) {
		g.Current = Position{x: g.Current.x, y: g.Current.y + g.Speed}
	} else if ebiten.IsKeyPressed(ebiten.KeyDown) {
		g.Current = Position{x: g.Current.x, y: g.Current.y - g.Speed}
	} else if ebiten.IsKeyPressed(ebiten.KeyLeft) {
		g.Current = Position{x: g.Current.x - g.Speed, y: g.Current.y}
	} else if ebiten.IsKeyPressed(ebiten.KeyRight) {
		g.Current = Position{x: g.Current.x + g.Speed, y: g.Current.y}
	}

	return nil
}

func (g Game) Draw(screen *ebiten.Image) {
	_ = screen.Fill(color.Black)
	ebitenutil.DrawRect(screen, float64(g.Current.x), float64(g.Current.y), 20, 20, color.RGBA{255, 0, 0, 255})
}

func (g Game) Layout(outsideWidth, outsideHeight int) (int, int) {
	return ScreenWidth, ScreenHeight
}

func main() {
	if err := ebiten.RunGame(NewGame()); err != nil {
		panic(err)
	}
}
