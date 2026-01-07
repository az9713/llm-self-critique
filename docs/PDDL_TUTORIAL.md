# PDDL Tutorial

A beginner-friendly guide to Planning Domain Definition Language (PDDL), the formal language used by this platform.

## Table of Contents

1. [What is PDDL?](#what-is-pddl)
2. [Why Learn PDDL?](#why-learn-pddl)
3. [PDDL Structure Overview](#pddl-structure-overview)
4. [Part 1: Domain Definition](#part-1-domain-definition)
5. [Part 2: Problem Definition](#part-2-problem-definition)
6. [Complete Example: Blocksworld](#complete-example-blocksworld)
7. [Common Patterns](#common-patterns)
8. [Debugging PDDL](#debugging-pddl)
9. [Advanced Features](#advanced-features)
10. [PDDL in This Platform](#pddl-in-this-platform)

---

## What is PDDL?

**Planning Domain Definition Language (PDDL)** is a standardized language for describing planning problems. Think of it as a precise way to tell a computer:

1. What **things** exist in your world
2. What **actions** can be performed
3. What **conditions** must be true before an action
4. What **changes** when an action is performed
5. What you're **starting with** and what you **want to achieve**

### A Simple Analogy

Imagine explaining a board game to someone:

- **Objects**: "There are pieces, squares, and players"
- **Predicates**: "A piece can be ON a square, a square can be EMPTY"
- **Actions**: "You can MOVE a piece from one square to another"
- **Preconditions**: "You can only move if the destination square is empty"
- **Effects**: "After moving, the old square is empty, the new square has the piece"

PDDL is just a formal way to write this down.

---

## Why Learn PDDL?

While this platform accepts natural language, understanding PDDL helps you:

1. **Debug** when plans don't work as expected
2. **Fine-tune** domain definitions for better results
3. **Export** plans to other planning tools
4. **Understand** what the AI is actually doing

---

## PDDL Structure Overview

A complete PDDL specification has two files:

```
┌─────────────────────────────────┐
│         DOMAIN FILE            │
│  (What's possible in general)  │
│                                │
│  - Types of objects            │
│  - Properties (predicates)     │
│  - Available actions           │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│        PROBLEM FILE            │
│  (A specific situation)        │
│                                │
│  - Actual objects              │
│  - Initial state               │
│  - Goal state                  │
└─────────────────────────────────┘
```

---

## Part 1: Domain Definition

### Basic Structure

```lisp
(define (domain domain-name)
  (:requirements :strips)
  (:types ...)           ; Optional: Define object types
  (:predicates ...)      ; Properties and relationships
  (:action ...)          ; What can be done
  (:action ...)          ; More actions...
)
```

### Requirements

The `:requirements` section declares what PDDL features you're using:

```lisp
(:requirements :strips)           ; Basic PDDL
(:requirements :strips :typing)   ; With typed objects
```

Common requirements:
- `:strips` - Basic actions with preconditions and effects
- `:typing` - Objects can have types
- `:equality` - Can test if two objects are the same
- `:negative-preconditions` - Can require something to NOT be true

### Predicates

Predicates describe properties and relationships. They're either **true** or **false**.

```lisp
(:predicates
  (on ?block1 ?block2)    ; block1 is on top of block2
  (clear ?block)          ; nothing is on top of block
  (ontable ?block)        ; block is on the table
  (holding ?block)        ; robot arm is holding block
  (handempty)             ; robot arm is empty
)
```

**Syntax breakdown:**
- `?` prefix means it's a variable (placeholder)
- `(on ?x ?y)` means "x is on y" - a relationship between two things
- `(clear ?x)` means "x is clear" - a property of one thing
- `(handempty)` - a property with no parameters (global state)

### Actions

Actions change the world state. Each action has:
- **Parameters**: What objects are involved
- **Preconditions**: What must be true before the action
- **Effects**: What changes after the action

```lisp
(:action pick-up
  :parameters (?block)
  :precondition (and
    (clear ?block)       ; nothing on top
    (ontable ?block)     ; block is on table
    (handempty)          ; arm is free
  )
  :effect (and
    (holding ?block)           ; now holding it
    (not (clear ?block))       ; no longer clear (we have it)
    (not (ontable ?block))     ; no longer on table
    (not (handempty))          ; arm is no longer empty
  )
)
```

**Understanding effects:**
- Positive effects: Things that become TRUE
- Negative effects: Things that become FALSE (using `not`)

### Logical Operators

PDDL uses these operators:

| Operator | Meaning | Example |
|----------|---------|---------|
| `and` | All must be true | `(and (clear ?x) (handempty))` |
| `or` | At least one true | `(or (ontable ?x) (on ?x ?y))` |
| `not` | Must be false | `(not (holding ?x))` |
| `imply` | If A then B | `(imply (heavy ?x) (use-crane ?x))` |
| `exists` | There exists some | `(exists (?y) (on ?x ?y))` |
| `forall` | For all objects | `(forall (?y) (not (on ?y ?x)))` |

---

## Part 2: Problem Definition

### Basic Structure

```lisp
(define (problem problem-name)
  (:domain domain-name)    ; Which domain to use
  (:objects ...)           ; Actual objects in this problem
  (:init ...)              ; Starting state
  (:goal ...)              ; What we want to achieve
)
```

### Objects

List all the actual objects in your problem:

```lisp
(:objects
  blockA blockB blockC    ; Three blocks
)
```

With types:
```lisp
(:objects
  blockA blockB blockC - block
  table1 - surface
)
```

### Initial State

List all the predicates that are TRUE at the start:

```lisp
(:init
  (ontable blockA)        ; A is on the table
  (ontable blockB)        ; B is on the table
  (on blockC blockA)      ; C is on top of A
  (clear blockB)          ; Nothing on B
  (clear blockC)          ; Nothing on C
  (handempty)             ; Arm is empty
)
```

**Important**: Anything not listed is assumed FALSE.

### Goal State

What must be true at the end:

```lisp
(:goal (and
  (on blockA blockB)      ; A must be on B
  (on blockB blockC)      ; B must be on C
))
```

---

## Complete Example: Blocksworld

The classic AI planning domain. You have blocks and a robot arm. Stack blocks to achieve a goal configuration.

### Domain File

```lisp
(define (domain blocksworld)
  (:requirements :strips)

  (:predicates
    (on ?x ?y)        ; x is directly on top of y
    (ontable ?x)      ; x is on the table
    (clear ?x)        ; nothing is on top of x
    (holding ?x)      ; the arm is holding x
    (handempty)       ; the arm is empty
  )

  ; Pick up a block from the table
  (:action pick-up
    :parameters (?block)
    :precondition (and
      (clear ?block)
      (ontable ?block)
      (handempty)
    )
    :effect (and
      (holding ?block)
      (not (clear ?block))
      (not (ontable ?block))
      (not (handempty))
    )
  )

  ; Put down a block on the table
  (:action put-down
    :parameters (?block)
    :precondition (holding ?block)
    :effect (and
      (clear ?block)
      (handempty)
      (ontable ?block)
      (not (holding ?block))
    )
  )

  ; Stack a block on another block
  (:action stack
    :parameters (?top ?bottom)
    :precondition (and
      (holding ?top)
      (clear ?bottom)
    )
    :effect (and
      (on ?top ?bottom)
      (clear ?top)
      (handempty)
      (not (holding ?top))
      (not (clear ?bottom))
    )
  )

  ; Unstack a block from another block
  (:action unstack
    :parameters (?top ?bottom)
    :precondition (and
      (on ?top ?bottom)
      (clear ?top)
      (handempty)
    )
    :effect (and
      (holding ?top)
      (clear ?bottom)
      (not (on ?top ?bottom))
      (not (clear ?top))
      (not (handempty))
    )
  )
)
```

### Problem File

```lisp
(define (problem blocks-problem-1)
  (:domain blocksworld)

  (:objects blockA blockB blockC)

  ; Initial: A on table, B on A, C on table
  ;    [B]
  ;    [A]  [C]
  ;   ─────────
  (:init
    (ontable blockA)
    (ontable blockC)
    (on blockB blockA)
    (clear blockB)
    (clear blockC)
    (handempty)
  )

  ; Goal: A on B on C
  ;    [A]
  ;    [B]
  ;    [C]
  ;   ─────
  (:goal (and
    (on blockA blockB)
    (on blockB blockC)
  ))
)
```

### Solution Plan

```
(unstack blockB blockA)  ; Pick up B from A
(put-down blockB)        ; Put B on table
(pick-up blockC)         ; Pick up C
(stack blockC blockB)    ; Wait, this is wrong direction!
```

Correct solution:
```
(unstack blockB blockA)  ; Pick up B from A
(put-down blockB)        ; Put B on table
(pick-up blockB)         ; Pick up B
(stack blockB blockC)    ; Put B on C
(pick-up blockA)         ; Pick up A
(stack blockA blockB)    ; Put A on B
```

---

## Common Patterns

### Pattern 1: Resource Consumption

```lisp
(:predicates
  (has-fuel ?vehicle)
  (at ?vehicle ?location)
)

(:action drive
  :parameters (?v ?from ?to)
  :precondition (and
    (at ?v ?from)
    (has-fuel ?v)
  )
  :effect (and
    (at ?v ?to)
    (not (at ?v ?from))
    (not (has-fuel ?v))    ; Fuel is consumed
  )
)
```

### Pattern 2: Conditional Effects

When an action has different effects based on conditions:

```lisp
(:action open-door
  :parameters (?door)
  :precondition (closed ?door)
  :effect (and
    (open ?door)
    (not (closed ?door))
    (when (locked ?door)      ; Conditional
      (not (locked ?door))    ; Only if it was locked
    )
  )
)
```

### Pattern 3: Mutual Exclusion

When something can only be in one state:

```lisp
; A light is either on or off
(:action turn-on
  :parameters (?light)
  :precondition (off ?light)
  :effect (and
    (on ?light)
    (not (off ?light))
  )
)
```

### Pattern 4: Capacity Constraints

```lisp
(:predicates
  (in ?item ?container)
  (space-available ?container)
)

(:action load
  :parameters (?item ?container)
  :precondition (and
    (space-available ?container)
    (not (in ?item ?container))
  )
  :effect (and
    (in ?item ?container)
    (not (space-available ?container))  ; Container now full
  )
)
```

---

## Debugging PDDL

### Common Errors

**1. Precondition Never Satisfied**
```lisp
; Error: No action makes (ready ?x) true
(:action process
  :precondition (ready ?x)  ; Nothing produces this!
  ...
)
```
Fix: Add an action that creates the required precondition.

**2. Missing Negative Effect**
```lisp
; Bug: Block is both on table AND being held
(:action pick-up
  :effect (holding ?block)
  ; Missing: (not (ontable ?block))
)
```

**3. Inconsistent Initial State**
```lisp
(:init
  (on blockA blockB)
  (clear blockB)    ; Contradiction! B has A on it
)
```

**4. Impossible Goal**
```lisp
(:goal (and
  (holding blockA)
  (handempty)       ; Can't hold something AND have empty hands
))
```

### Validation Checklist

1. Every predicate in preconditions appears in some effect
2. Every predicate in goals appears in initial state OR some effect
3. No contradictions in initial state
4. Goal is achievable (check each predicate)
5. All objects referenced exist in `:objects`

---

## Advanced Features

### Typed PDDL

Group objects by type for cleaner definitions:

```lisp
(define (domain logistics)
  (:requirements :strips :typing)

  (:types
    vehicle location package - object
    truck airplane - vehicle
    city airport - location
  )

  (:predicates
    (at ?v - vehicle ?l - location)
    (in ?p - package ?v - vehicle)
  )

  (:action load-truck
    :parameters (?p - package ?t - truck ?l - location)
    :precondition (and (at ?t ?l) (at ?p ?l))
    :effect (and (in ?p ?t) (not (at ?p ?l)))
  )
)
```

### Numeric Fluents

For quantities that change:

```lisp
(:requirements :strips :fluents)

(:functions
  (fuel-level ?vehicle)
  (distance ?from ?to)
)

(:action drive
  :parameters (?v ?from ?to)
  :precondition (>= (fuel-level ?v) (distance ?from ?to))
  :effect (decrease (fuel-level ?v) (distance ?from ?to))
)
```

### Durative Actions

For actions that take time:

```lisp
(:durative-action fly
  :parameters (?plane ?from ?to)
  :duration (= ?duration 100)
  :condition (and
    (at start (at ?plane ?from))
    (over all (have-fuel ?plane))
  )
  :effect (and
    (at start (not (at ?plane ?from)))
    (at end (at ?plane ?to))
  )
)
```

---

## PDDL in This Platform

### How the Platform Uses PDDL

1. **You describe** your problem in natural language
2. **AI generates** PDDL domain and problem definitions
3. **Validation** checks PDDL for errors
4. **Planning** generates a solution
5. **Self-critique** verifies each action's preconditions

### Viewing Generated PDDL

1. Navigate to your domain
2. Click "View PDDL" or "Export"
3. Review both domain and problem files

### Editing PDDL Directly

For advanced users:
1. Go to domain settings
2. Select "Advanced Mode"
3. Edit PDDL directly
4. Click "Validate" to check for errors

### Common Customizations

**Adding constraints:**
```lisp
; Original
(:action move :parameters (?from ?to) ...)

; With constraint
(:action move
  :parameters (?from ?to)
  :precondition (and
    (not (= ?from ?to))    ; Can't move to same place
    ...
  )
)
```

**Optimizing for efficiency:**
```lisp
; Add parallel capability
(:predicates
  (can-parallel ?action1 ?action2)
)
```

---

## Quick Reference

### PDDL Syntax Summary

```lisp
; Domain
(define (domain NAME)
  (:requirements :strips)
  (:predicates (pred-name ?param1 ?param2))
  (:action action-name
    :parameters (?p1 ?p2)
    :precondition (and (pred1 ?p1) (pred2 ?p2))
    :effect (and (pred3 ?p1) (not (pred1 ?p1)))
  )
)

; Problem
(define (problem NAME)
  (:domain DOMAIN-NAME)
  (:objects obj1 obj2 obj3)
  (:init (pred1 obj1) (pred2 obj1 obj2))
  (:goal (and (pred3 obj2) (pred4 obj3)))
)
```

### Operators

| Syntax | Meaning |
|--------|---------|
| `?x` | Variable |
| `(and ...)` | All conditions |
| `(or ...)` | Any condition |
| `(not ...)` | Negation |
| `(= ?x ?y)` | Equality |
| `(when cond effect)` | Conditional effect |

---

## Further Reading

- **PDDL Reference**: [planning.wiki/ref/pddl](https://planning.wiki/ref/pddl)
- **Classic Planners**: Fast Downward, STRIPS
- **This Platform's Validation**: See [API Reference](API_REFERENCE.md)

---

*Last updated: January 2026*
