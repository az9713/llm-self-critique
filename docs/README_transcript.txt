https://www.youtube.com/watch?v=0x8JoBLV-8c&t=8s

"We demonstrate an approach for LLMs to critique their own answers with the goal of enhancing their performance that leads to significant improvements over established planning benchmarks. 

Despite the findings of earlier research that has cast doubt on the effectiveness of LLMs leveraging self critique methods, we show significant performance gains on planning datasets in the Blocksworld domain through intrinsic self-critique, without external source such as a verifier. "
Quote by Google DeepMind (see below)

All rights w/ authors:
"Enhancing LLM Planning Capabilities through Intrinsic Self-Critique"
Bernd Bohnet1, Pierre-Alexandre Kamienny1, Hanie Sedghi1, Dilan Gorur1, Pranjal Awasthi1, Aaron Parisi1, Kevin Swersky1, Rosanne Liu1, Azade Nova1 and Noah Fiedel1
from
1 Google DeepMind
arXiv:2512.24103



Transcript


0:00
Hello community. So great that you are
0:02
back. Today we talk about something
0:04
brand new in context symbolic AI.
0:08
Welcome to my channel Discovery. We have
0:10
a look at the latest research paper. Now
0:12
Google goes to extremes now and I love
0:16
it because I have to explain what you're
0:20
going to see in the following study. Now
0:23
you know we do have neuro symbolic AI as
0:26
the future of AI in 2026. No. So this
0:29
means we do have an EI system with a
0:32
beautiful linguistic system that can
0:34
write and read beautifully and write
0:37
poems and give beautiful long
0:39
explanations. But whenever you need
0:41
reasoning, whenever you need finance,
0:43
whenever you need calculation, whenever
0:45
you need science, you have to have a
0:48
logic solver. A logic solver is a
0:50
deterministic machine. An EI is a
0:53
probabilistic machine. And guess what?
0:55
In finance, you want a deterministic
0:57
solver. So we moved the intelligence
1:00
over from AI to our logic solver that we
1:03
started to build in 1980s and the base
1:06
of all the supercomputers we have today
1:08
that are ni and they extreme efficient
1:11
and this is here the human knowledge if
1:14
you want in lean for up to whatever you
1:17
like as a solver.
1:19
Now as it turns out there are some
1:21
companies I'm not going to mention any
1:24
that says no AI we have to bring the
1:27
intelligence into the neural network and
1:30
we have to build huge AI system we have
1:33
not to build any open AI system because
1:35
you don't have the Nvidia card for this
1:37
no we have to build the AI system with
1:39
trillions of free trainable parameters
1:41
and even more so all whatever there is
1:46
the should learn it and the logic solver
1:48
is just for some extreme mathematical,
1:50
physical, chemical, financial task that
1:52
even this AI cannot solve. Now,
1:55
interestingly, I don't know if you have
1:57
noticed it for this kind of AI, we need
2:00
huge data center. So, let's just imagine
2:02
that those companies I'm not going to
2:04
mention,
2:05
they invested heavily billions and
2:08
billions of dollars in data center. And
2:10
now the question is should the next
2:11
generation of EI be A on the left side
2:16
or B on the right side? Now Google says
2:20
now and I think this is just this paper
2:22
is kind of a big smile if you understand
2:25
to read this paper. Google says now you
2:28
know what let's build it. Let's build an
2:30
in context symbolic AI so that we see
2:34
exactly what we achieve here if we bring
2:36
the intelligence all the intelligence
2:38
into an AI
2:41
and we need I don't know how many
2:43
hundreds and thousands of data center on
2:45
our beautiful planet.
2:47
So here we have it. This is a study from
2:49
the almost the last day in December of
2:51
2025. Google deep mind enhancing the LLM
2:54
planning capabilities through some
2:56
intrinsic self critique and you see I
3:00
already smile because it is such a
3:02
beautiful paper. Now this preprints
3:05
presents now a robust demonstration and
3:07
you can do this at home because Google
3:09
gives us here an in context symbolic
3:12
compilation. So you can go you can copy
3:14
here the prompt from the paper and you
3:16
can just add it here in context into
3:18
your prompt here. But careful you have
3:21
to have a symbolic integration now into
3:23
your AI machine and Google shows us how
3:26
you can do this. Now Google tells us you
3:29
know there has always been two
3:30
possibilities here. We have the pure
3:33
neural networks here which rely on
3:35
probability statistical calculation. And
3:38
then we have the symbolic systems no
3:39
with logic and rules and who needs this
3:41
no or finance and you know correctness
3:44
and constraints and the dogma was that
3:46
L&Ms are fuzzy no and cannot handle the
3:48
rigid unforgiving logic here especially
3:51
in the planning phase. If you give here
3:53
a complex prompt to your AI to your L&M
3:57
and the has problems to come up with a
4:00
plan how to solve this is a five-step
4:02
plan a sevenstep plan and is it today we
4:06
say hey we need now here an external
4:08
calculator an external Python script an
4:10
external C++ computer simulation of a
4:13
fluid dynamic of a material science of a
4:16
financial calculation that is done here
4:17
on deteministic system and not on AI
4:20
system that is hallucinating and giving
4:23
me a statistical result.
4:26
Now, Deep Mind has said let's do it.
4:29
what what we have to do to make AI the
4:31
LLM now let's say up to almost 90%
4:36
reliable like a deterministic system no
4:38
and they say let's force the to the max
4:41
let's go extreme so deep mind decided to
4:44
you force a new network to run a
4:46
symbolic program purely through
4:48
inference
4:50
so no lean force server no other C++
4:53
environment you stick with the and you
4:57
brute force it Now that it does see
5:00
symbolic programming. So you have of
5:02
course to inject if you want the formal
5:04
physics of the world and you do this in
5:06
PDDL into the context window which is a
5:09
challenge in itself but the mind show us
5:11
it can be done. The LLM stops acting now
5:14
as a text generator this beautiful
5:16
linguistic log language model and it
5:19
starts now to act here as a latent state
5:23
emulator based on probabilistic and
5:25
statistical features.
5:28
It does not just predict now the next
5:30
token. It really now compiles the logic
5:33
on the constraint manifold in real time.
5:37
So really Google goes extreme. Google
5:40
implies that the reasoning in the LLM is
5:42
not missing.
5:45
So you can force this LLM into
5:48
reasoning. The reasoning will emerge but
5:50
only on a condition. It requires a
5:53
specific runtime environment. And this
5:55
is the PDDDL domain definition to be
5:58
active in the eye not in the solver. And
6:01
you might say but this sounds crazy.
6:03
Yeah. But this I think is exactly the
6:06
task that Google shows us. No. So to
6:09
understand PDL planning domain
6:11
definition I have a particular video on
6:12
this. So I assume you are familiar with
6:14
it. Think of it as defining now the
6:17
physics engine. No or the rule book of a
6:20
very specific universe. And your
6:22
universe can be really small. It can be
6:24
just this game the tower of Hanoi or it
6:26
can be just chess or go. So your
6:29
universe can be really small and tiny
6:31
and you define all the rules and now you
6:34
have to communicate this rules into your
6:38
LLM.
6:40
So
6:41
this is now the idea. You don't tell the
6:43
LLM what to solve. No, you just give it
6:46
the domain file of PDDDL. You simply
6:49
define what is possible in your universe
6:52
of the tower of Hanoi. And you have now
6:55
really absolutely carefully to list the
6:57
object that exist, the facts that can be
7:00
true in your universe of the tower of
7:02
Hanoi and the actions that can change
7:06
those fact that can be taken and maybe
7:08
some action that you you do not allow to
7:11
happen.
7:12
So you see you extremely limit the
7:16
solution space giving now in the prompt
7:19
in the in context learning you provide
7:22
now here the if you want PDDDL domain
7:26
file into the AI system itself and not
7:30
into the solver. So Google is kind of
7:32
choking here with us but in a clever
7:34
way. So if you're not familiar with it
7:36
just want to give you an example. If you
7:38
have a PDDL domain definition what is
7:40
it? Imagine you have a robot that moves
7:43
between two rooms and it picks up and
7:46
drops off a ball in room A and in room
7:48
B. Great. So this is it. This is here
7:51
for example in list here you have here
7:53
your type you have your predicates you
7:55
have your action you have an action move
7:56
A. This means move and you have an
7:58
action move B pick up. And this is the
8:01
definition of all the action and the
8:03
universe is defined because it only
8:05
consists of two rooms and in these rooms
8:08
only the action move and the action
8:10
pickup existent.
8:13
Now imagine you would have to do this
8:15
here for a real world environment. You
8:17
would go crazy. But Google shows us hey
8:20
look this is here simple PDDL. No. So
8:22
what is not a breakdown of the logic?
8:24
You have the predicates. These are the
8:25
state variables. Those are the only
8:27
thing the eyes allowed to know about the
8:29
world. No, for example, that hand empty
8:32
robot is a boo switch and it is either
8:34
true or false. And then as I showed you
8:36
the actions, no, the operators. This is
8:38
where the if you want the neuro symbolic
8:40
magic happens now in the paper. No, and
8:42
you have the precondition. This is where
8:43
the guard rails before the robot can
8:47
execute a single move the PDDL engine
8:50
checks. And this is now not in an
8:51
external server, but in the eye is at
8:54
robot from true. And if the robot is in
8:57
room A and it tries to move from room
8:59
into the room B, the action is blocked.
9:01
So the paper forces the LLM to
9:04
explicitly check all the universal
9:08
condition before it decides on anything.
9:11
So it is not that you have the
9:12
intelligence in the eye that just says
9:14
hey yeah so now hallucinate if the robot
9:16
is moving from room A into room B. No
9:18
way. You have rules. You have to follow
9:20
the rules. You have to follow, you have
9:22
to check the preconditions and then
9:24
maybe you allowed to make a move that is
9:26
a deterministic move and then if the
9:29
actions succeed the world state is
9:31
updated.
9:33
So at robot room A is deleted and at
9:36
robot room B is now added. So we have
9:38
now a new state of the system. The robot
9:40
is in room B.
9:42
So you see what Google is doing here. It
9:45
goes to the extreme. It really now
9:47
integrates here the intelligence back
9:49
into the AI and shows what's happening.
9:52
So by pasting here this code above into
9:54
now your prompt to your AI the orers
9:57
force now the LLM to run the following
9:59
logic. I want TSSTI to move. So let me
10:03
check here the domain definition. Does
10:06
connect for example connect kitchen
10:07
bathroom exist in my preconditions? No.
10:10
Then this action is invalid and I must
10:12
find another path. This is the internal
10:14
reasoning of our AI robot. Yeah, it says
10:17
I don't trust anything any sensors I
10:19
have nothing I have a predefined solid
10:22
deterministic logic and now I solve this
10:25
with my AI neural brain.
10:29
Now the author said okay we will not
10:31
come to a conclusion so we have to
10:33
optimize this system and they invented
10:35
an intrinsic self-critique you know
10:38
critique system but this intrinsic self
10:41
critique is something special no because
10:43
step one is the plan generation no we
10:45
make a plan how to solve this is our
10:47
strategy as an AI problem the model
10:50
receives your problem instance here for
10:51
example in tow of Hanoi stack the block
10:54
A on block B and some few short examples
10:56
now and now it generates a candidate
10:58
Plan B P for planning. Step two is then
11:03
a self critique. The model is now
11:05
prompted to critique its own plan which
11:07
is always a good idea. No, but this is
11:10
not the generic hey is this a correct
11:12
move prompt. This prompt again includes
11:15
the domain definition in the PDDDL
11:17
format in our planning domain definition
11:20
language.
11:22
And you know in this definition lists
11:24
every action its parameter its
11:26
precondition what must be true on the
11:28
precondition before it can take any
11:31
action and all the effects what comes
11:34
true afterwards. So we limit here the
11:37
possibility of an AI to an extreme
11:39
effect here just on more or less two
11:41
axis here to a two dimensional manifold.
11:43
No and we provide instruction to this
11:46
AI. So for each action take the action
11:49
and the precondition verify that all the
11:52
preconditions are met and only then you
11:54
allow to apply the action and provide
11:55
the resulting state because now we have
11:57
changed the state of the system and we
11:59
have a dynamic state development.
12:02
Then step three state tracking and
12:05
verification.
12:07
If the LM encounters here any violation
12:10
it must explicitly flag it and say this
12:12
plan is wrong. And then you have the
12:14
revision. So all the critique returns as
12:17
the flag wrong and the eye is now able
12:20
to learn from this plan where it failed
12:23
previously. Now they decided to go
12:26
another let's call it an extreme step
12:28
okay let's do have as another
12:30
self-consistency check of the eye the
12:33
eye should be autonomous. So we will
12:35
have an ensembling critique with a
12:38
majority voting of the critique step. So
12:41
you run the critique prompt five times
12:43
in a row and if the majority of the AI
12:46
and now hopefully you have the same AI
12:48
voting just five times in a row says
12:50
correct the loop ends and if the
12:52
majority says wrong the loop continues.
12:56
Now with this complete construct, Google
13:00
could
13:02
increase the accuracy of a block world
13:04
03 to five blog only from 85%
13:07
performance with only a single critique
13:10
step in this to an almost 90%
13:14
with a voting majority voting critique
13:16
step as I just showed you. So we did
13:18
achieve what we set out to do. We built
13:20
an EI that without an external solver,
13:23
without an external logic solver is able
13:26
to do this. But the way we had to build
13:30
and wire and rewire and validate and
13:33
revalidate and check and recheck and
13:35
critique five times in a row and have a
13:37
majority voting here. And if not, it
13:40
goes back into the course loop. You see
13:43
what we have to do to achieve 90% when
13:47
we have three to five blocks in our
13:50
universe that we can move. Now imagine
13:52
this on a real world example. Imagine
13:55
this here on I don't know a autonomous
13:58
vehicle driving system.
14:01
This system would go crazy. This is
14:04
inefficiency squared. But what are the
14:07
insights that Google shows us? And you
14:09
have to read a little bit here at the
14:11
end of this uh preprint.
14:14
An intrinsic verification works if you
14:17
do it often enough deep enough. If you
14:20
restrict the solution space massively
14:22
only to two axis, you have that the
14:25
verification can work on a probabilistic
14:28
system.
14:29
So the paper kind of quotation mark
14:32
overturns here the assumption that LLMs
14:34
are incapable of selfcorrection in the
14:36
reasoning tasks in reasoning tasks. No
14:40
and they argue maybe the failure of
14:42
previous attempts was likely due to lazy
14:44
prompting
14:46
think about as a joke by Google because
14:49
now with PTDDL where you extremely limit
14:51
the universe yet to three blocks now the
14:55
selfcorrection reasoning in EI is
14:57
working.
15:00
It says we have to provide to the eye
15:03
the precondition of the universe of the
15:05
three blocks what moves are allowed. So
15:08
the mechanism of success is now forcing
15:11
the eye model to attend to all the
15:13
precondition all the constraint rather
15:16
just give it hey your goal is to solve
15:18
this task because if you just say your
15:21
goal is to solve this task the will fail
15:24
without here a logic solver on its side.
15:27
Yeah. So therefore, if you want just the
15:29
eye without a logic solver, you have to
15:32
take care about the preconditions
15:35
and you have to do a state tracking as a
15:38
proxy for the world models that you
15:39
don't have. So by outputting the state
15:42
after every single little detail step,
15:45
the LLM effectively simulates here in a
15:49
listed world model in its context
15:52
window. Now it works with three to five
15:55
blocks in your universe. Imagine a real
15:57
world.
15:59
So Google show showed us here there's a
16:02
shift from an outcomebased verification
16:04
to a process-based verification where
16:06
the AI is more or less continuously
16:08
verifying its own result and verifying
16:11
its own result and verifying its own
16:13
result.
16:15
But the nice thing is that the method
16:17
forces here state tracking here from a
16:20
time s here to predict here at at time t
16:22
+ one. So the model explicitly tracks
16:25
here the hidden variables of the world
16:28
like I showed you here our pdl holding
16:30
block a is true and it creates a digital
16:33
twin of the problem in its context
16:34
window and updates the state vector
16:37
after every move.
16:40
So if you want you can prove now that
16:42
the transformer can maintain a coherent
16:45
internal state representation in its
16:48
context window over long horizon. If you
16:51
just force the model to the extreme with
16:54
this limitations with this whatever you
16:57
will call it here to externalize here
17:01
the complete reasoning process. It is
17:04
not that you give it a template. We are
17:06
a little bit more generous than just a
17:08
template. No, we just define whatever is
17:11
possible in this universe but it is real
17:14
close to a template. No, and then then
17:17
we can expect the reasoning process from
17:19
an eye that is really correct and you
17:22
have almost no hallucination and you
17:24
achieve 90% accuracy.
17:27
Now at the end I have to have a critical
17:28
view on this. No, I mean it's I would
17:32
not call it a joke but it's such a
17:34
beautiful example by Google and only
17:36
Google can do this. It reveals the
17:38
inefficiency of all AI compute of all
17:42
probabilistic
17:43
compute if it is not connected real
17:46
neurosy symbolic also to a deterministic
17:49
load computer. So to emulate a simple
17:52
logical check here that I don't know a
17:54
1980s symbolic solver could do in
17:57
microsconds. Yeah this was like a a
18:00
table calculator the size.
18:02
This method now from Google at the end
18:03
of 2025 requires billions of flops and
18:07
massive token overhead and a note of
18:09
eight of the latest Nvidia GPU running
18:12
max
18:14
and I think it highlights a critical
18:16
inefficiency in an absolute beautiful
18:18
way. What we are doing we are using here
18:21
this Nvidia AI superco computer to
18:25
simulate a pocket calculator.
18:28
So while we can achieve this and Google
18:30
showed us in this paper we can achieve
18:32
it if we limit everything here
18:35
absolutely and we force here the LLM not
18:38
to sync independently but only allowed
18:41
along the axis that we allow the LLM to
18:43
sync we can achieve a 90% accuracy but
18:47
while efficient it suggests that the
18:49
future architectures I mean just as idea
18:52
no should be maybe hybrid no or you will
18:55
hit a compute all trying to simulate
18:58
logic through pure attention mechanism
19:01
in pure AI system. I think you cannot
19:03
put it you cannot put this more
19:05
elegantly like Google did here in this
19:08
study. No. And how do you overcome a
19:11
compute wall? Yeah. You build more data
19:13
centers and you don't use your brain.
19:17
So if this is now this is for you for AI
19:19
researcher what are actionable
19:21
applications that we can get out of this
19:23
paper because okay it shows us something
19:26
if you understand it if not it just
19:28
tells us hey stop building chains of
19:29
sort start building state machines
19:33
tells us because if you are building
19:35
autonomous agents your current prompt
19:37
structure that you're currently
19:38
prompting your agents are failing and we
19:41
are not talking about 80% we're talking
19:44
below 80% u success rate because they
19:47
are stateless. So you are asking more or
19:49
less the eye model to let's call it
19:52
hallucinate a path to the defined goal
19:55
and the is absolutely free to define the
19:58
path here on 10,000 different
20:01
trajectories to the goal.
20:04
This is all depending here on the
20:05
pre-training of the eye of the
20:07
post-training of the eye and hopefully
20:09
you do not have any calcul any
20:11
hallucination in this step and you want
20:13
to exclude all deterministic
20:15
calculations here on an external solver
20:19
like lean 4 then you asking them well
20:22
really to hallucinate because if you go
20:24
into harder and harder reasoning tasks
20:27
the probability of hallucination
20:29
increases significantly and the only
20:32
counter measure you can have is you
20:33
verify every step of the eye with a
20:36
verifier and then of this verifier you
20:38
have another verifier and another
20:40
verifier verifier is the verifier of the
20:42
verifier and you get the idea so what is
20:44
the upgrade you should do formalize your
20:46
domain don't just describe the task in
20:49
English define all the invariance that
20:51
you as a human are able to understand in
20:52
your system for example in code
20:54
generation it is easy no you just say
20:56
the system hey you cannot call a
20:58
function that has not been imported
21:00
forget about it or modify your system
21:02
prompt to require by a state transition
21:05
output like I have shown you in my
21:07
tests. No, the model must output the
21:09
after state of variables following every
21:13
action. Now some of the latest AI
21:16
models, they don't want to do this. No,
21:18
incorrect. The the creators of those
21:22
models said, hm, we don't want this
21:24
function to be implemented in our latest
21:27
AI models. Of course,
21:30
and then the third part is the compiler
21:32
loop.
21:33
implement really an intrinsic critique
21:35
as a filter because if the model cannot
21:37
derive the next state from the current
21:39
state using the rules the generation is
21:41
simply rejected and you are safe. So you
21:45
see it can be so simple but there are
21:48
all the reasons in this world that some
21:51
global corporation
21:53
might not be interested to make it for
21:55
financial reason or for strategic reason
21:57
or for IPO reasons to make it that
21:59
simple and therefore I think this
22:02
publication by Google is simply a chef's
22:05
kiss. I hope you enjoyed it. I hope you
22:07
had a little bit of fun with this. Maybe
22:09
you have some new insights. Anyway, I
22:11
hope you subscribe, become a member, and
22:13
I see you in my next video.
