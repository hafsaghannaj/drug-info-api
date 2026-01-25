// React Native rhythm game demo with placeholder audio and basic scoring

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';
import { Audio } from 'expo-av';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const LANES = ['left', 'middle', 'right'];
const NOTE_TRAVEL_MS = 2500;
const HIT_WINDOW_MS = 140;
const NOTE_SIZE = 36;
const HIT_LINE_Y = SCREEN_HEIGHT * 0.75;

const LANE_X = {
  left: SCREEN_WIDTH * 0.2 - NOTE_SIZE / 2,
  middle: SCREEN_WIDTH * 0.5 - NOTE_SIZE / 2,
  right: SCREEN_WIDTH * 0.8 - NOTE_SIZE / 2,
};

const makeChart = () => {
  const chart = [];
  const noteCount = 28;
  const startAt = 1000;
  const gap = 550;
  for (let i = 0; i < noteCount; i += 1) {
    const lane = LANES[Math.floor(Math.random() * LANES.length)];
    chart.push({
      id: `note-${i}`,
      lane,
      time: startAt + i * gap,
      hit: false,
      missed: false,
    });
  }
  return chart;
};

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

export default function App() {
  const [notes, setNotes] = useState([]);
  const [gameState, setGameState] = useState('idle');
  const [score, setScore] = useState(0);
  const [streak, setStreak] = useState(0);
  const [misses, setMisses] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [sound, setSound] = useState(null);

  const startRef = useRef(null);
  const rafRef = useRef(null);
  const elapsedRef = useRef(0);

  useEffect(() => {
    return sound
      ? () => {
          sound.unloadAsync();
        }
      : undefined;
  }, [sound]);

  useEffect(() => {
    if (gameState !== 'playing') {
      return undefined;
    }

    const tick = (t) => {
      if (!startRef.current) {
        startRef.current = t;
      }
      const currentElapsed = t - startRef.current;
      elapsedRef.current = currentElapsed;
      setElapsed(currentElapsed);
      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [gameState]);

  useEffect(() => {
    if (gameState !== 'playing') {
      return undefined;
    }

    const missTimer = setInterval(() => {
      const now = elapsedRef.current;
      let missCount = 0;

      setNotes((prev) =>
        prev.map((note) => {
          if (!note.hit && !note.missed && now > note.time + HIT_WINDOW_MS) {
            missCount += 1;
            return { ...note, missed: true };
          }
          return note;
        })
      );

      if (missCount > 0) {
        setMisses((value) => value + missCount);
        setStreak(0);
      }
    }, 80);

    return () => clearInterval(missTimer);
  }, [gameState]);

  const playSong = async () => {
    if (sound) {
      await sound.unloadAsync();
      setSound(null);
    }

    const { sound: created } = await Audio.Sound.createAsync(
      require('./assets/song.wav')
    );
    setSound(created);
    await created.playAsync();
  };

  const startGame = async () => {
    setNotes(makeChart());
    setScore(0);
    setStreak(0);
    setMisses(0);
    setElapsed(0);
    startRef.current = null;
    setGameState('playing');
    await playSong();
  };

  const stopGame = async () => {
    if (sound) {
      await sound.stopAsync();
    }
    setGameState('finished');
  };

  const handleHit = (lane) => {
    if (gameState !== 'playing') {
      return;
    }

    const now = elapsedRef.current;
    let hitRegistered = false;

    setNotes((prev) => {
      let bestIndex = -1;
      let bestDistance = Infinity;

      prev.forEach((note, index) => {
        if (note.lane !== lane || note.hit || note.missed) {
          return;
        }
        const distance = Math.abs(note.time - now);
        if (distance <= HIT_WINDOW_MS && distance < bestDistance) {
          bestDistance = distance;
          bestIndex = index;
        }
      });

      if (bestIndex === -1) {
        return prev;
      }

      hitRegistered = true;
      const next = [...prev];
      next[bestIndex] = { ...next[bestIndex], hit: true };
      return next;
    });

    if (hitRegistered) {
      setScore((value) => value + 100);
      setStreak((value) => value + 1);
    } else {
      setMisses((value) => value + 1);
      setStreak(0);
    }
  };

  const activeNotes = useMemo(() => {
    return notes.filter((note) => {
      if (note.hit || note.missed) {
        return false;
      }
      const progress = (elapsed - (note.time - NOTE_TRAVEL_MS)) / NOTE_TRAVEL_MS;
      return progress >= -0.2 && progress <= 1.2;
    });
  }, [notes, elapsed]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Placeholder Rhythm Game</Text>
      <Text style={styles.subtitle}>Tap lanes on the hit line</Text>

      <View style={styles.statsRow}>
        <View style={styles.statBox}>
          <Text style={styles.statLabel}>Score</Text>
          <Text style={styles.statValue}>{score}</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statLabel}>Streak</Text>
          <Text style={styles.statValue}>{streak}</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statLabel}>Misses</Text>
          <Text style={styles.statValue}>{misses}</Text>
        </View>
      </View>

      <View style={styles.laneArea}>
        <View style={styles.hitLine} />
        {activeNotes.map((note) => {
          const progress = clamp(
            (elapsed - (note.time - NOTE_TRAVEL_MS)) / NOTE_TRAVEL_MS,
            0,
            1
          );
          const y = HIT_LINE_Y * 0.15 + progress * (HIT_LINE_Y - NOTE_SIZE);
          return (
            <View
              key={note.id}
              style={[
                styles.note,
                {
                  left: LANE_X[note.lane],
                  top: y,
                  opacity: 1 - Math.abs(progress - 0.5) * 0.2,
                },
              ]}
            />
          );
        })}

        <View style={styles.lanesRow}>
          {LANES.map((lane) => (
            <TouchableOpacity
              key={lane}
              style={styles.laneButton}
              onPress={() => handleHit(lane)}
              activeOpacity={0.7}
            >
              <Text style={styles.laneLabel}>{lane.toUpperCase()}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.controlsRow}>
        <TouchableOpacity
          style={[styles.controlButton, styles.playButton]}
          onPress={startGame}
          disabled={gameState === 'playing'}
        >
          <Text style={styles.controlText}>Start</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.controlButton, styles.stopButton]}
          onPress={stopGame}
          disabled={gameState !== 'playing'}
        >
          <Text style={styles.controlText}>Stop</Text>
        </TouchableOpacity>
      </View>

      {gameState === 'finished' ? (
        <Text style={styles.resultText}>Good run! Tap Start to try again.</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111318',
    alignItems: 'center',
    paddingTop: 60,
  },
  title: {
    color: '#f8f4ff',
    fontSize: 26,
    fontWeight: '700',
    marginBottom: 6,
  },
  subtitle: {
    color: '#a4a8b6',
    fontSize: 14,
    marginBottom: 20,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  statBox: {
    backgroundColor: '#1f2330',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  statLabel: {
    color: '#7b8194',
    fontSize: 12,
    marginBottom: 4,
  },
  statValue: {
    color: '#f8f4ff',
    fontSize: 18,
    fontWeight: '600',
  },
  laneArea: {
    width: '100%',
    flex: 1,
    alignItems: 'center',
    justifyContent: 'flex-start',
  },
  hitLine: {
    position: 'absolute',
    top: HIT_LINE_Y,
    width: SCREEN_WIDTH * 0.85,
    height: 2,
    backgroundColor: '#f06292',
    opacity: 0.8,
  },
  note: {
    position: 'absolute',
    width: NOTE_SIZE,
    height: NOTE_SIZE,
    borderRadius: NOTE_SIZE / 2,
    backgroundColor: '#ffb857',
    shadowColor: '#ffb857',
    shadowOpacity: 0.8,
    shadowRadius: 8,
  },
  lanesRow: {
    position: 'absolute',
    top: HIT_LINE_Y + 30,
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: SCREEN_WIDTH * 0.85,
  },
  laneButton: {
    flex: 1,
    marginHorizontal: 6,
    paddingVertical: 16,
    borderRadius: 14,
    backgroundColor: '#252a3a',
    alignItems: 'center',
  },
  laneLabel: {
    color: '#f8f4ff',
    fontWeight: '600',
    fontSize: 12,
    letterSpacing: 1,
  },
  controlsRow: {
    flexDirection: 'row',
    gap: 14,
    marginBottom: 18,
  },
  controlButton: {
    paddingVertical: 12,
    paddingHorizontal: 26,
    borderRadius: 20,
  },
  playButton: {
    backgroundColor: '#5ad2a4',
  },
  stopButton: {
    backgroundColor: '#e36c6c',
  },
  controlText: {
    color: '#111318',
    fontWeight: '700',
  },
  resultText: {
    color: '#b8bcd0',
    marginBottom: 24,
  },
});
