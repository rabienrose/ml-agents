using System;
using System.Security.Principal;
using Unity.MLAgents;
using Unity.MLAgents.Actuators;
using UnityEditor;
using UnityEngine;
using UnityEngine.EventSystems;
using Unity.MLAgents.Extensions.Match3;

namespace Unity.MLAgentsExamples
{
    enum State
    {
        Invalid = -1,

        FindMatches = 0,
        ClearMatched = 1,
        Drop = 2,
        FillEmpty = 3,

        WaitForMove = 4,

        NumSteps = 4
    }

    public class Match3Agent : Agent
    {
        [HideInInspector]
        public Match3Board Board;

        public float MoveTime = 1.0f;

        State m_CurrentState = State.FindMatches;
        float m_TimeUntilMove;

        private bool[] m_ValidMoves;
        private System.Random m_Random;
        private const float k_RewardMultiplier = 0.01f;

        void Awake()
        {
            Board = GetComponent<Match3Board>();
            m_ValidMoves = new bool[Move.NumEdgeIndices(Board.Rows, Board.Columns)];
            m_Random = new System.Random(Board.RandomSeed + 1);
        }

        public override void OnEpisodeBegin()
        {
            base.OnEpisodeBegin();

            Board.InitSettled();
            m_CurrentState = State.FindMatches;
            m_TimeUntilMove = MoveTime;
        }

        private void FixedUpdate()
        {
            if (Academy.Instance.IsCommunicatorOn)
            {
                FastUpdate();
            }
            else
            {
                AnimatedUpdate();
            }
        }

        void FastUpdate()
        {
            while (true)
            {
                var hasMatched = Board.MarkMatchedCells();
                if (!hasMatched)
                {
                    break;
                }
                var numMatched = Board.ClearMatchedCells();
                AddReward(k_RewardMultiplier * numMatched);
                Board.DropCells();
                Board.FillFromAbove();
            }

            while (true)
            {
                // Shuffle the board until we have a valid move.
                bool hasMoves = CheckValidMoves();
                if (hasMoves)
                {
                    break;
                }
                Board.InitSettled();
            }
            RequestDecision();

        }

        void AnimatedUpdate()
        {
            m_TimeUntilMove -= Time.deltaTime;
            if (m_TimeUntilMove > 0.0f)
            {
                return;
            }

            m_TimeUntilMove = MoveTime;

            var nextState = State.Invalid;
            switch (m_CurrentState)
            {
                case State.FindMatches:
                    var hasMatched = Board.MarkMatchedCells();
                    nextState = hasMatched ? State.ClearMatched : State.WaitForMove;
                    break;
                case State.ClearMatched:
                    var numMatched = Board.ClearMatchedCells();
                    AddReward(k_RewardMultiplier * numMatched);
                    nextState = State.Drop;
                    break;
                case State.Drop:
                    Board.DropCells();
                    nextState = State.FillEmpty;
                    break;
                case State.FillEmpty:
                    Board.FillFromAbove();
                    nextState = State.FindMatches;
                    break;
                case State.WaitForMove:
                    while (true)
                    {
                        // Shuffle the board until we have a valid move.
                        bool hasMoves = CheckValidMoves();
                        if (hasMoves)
                        {
                            break;
                        }
                        Board.InitSettled();
                    }
                    RequestDecision();

                    nextState = State.FindMatches;
                    break;
                default:
                    throw new ArgumentOutOfRangeException();
            }

            m_CurrentState = nextState;
        }

        bool CheckValidMoves()
        {
            int numValidMoves = 0;
            Array.Clear(m_ValidMoves, 0, m_ValidMoves.Length);

            for (var index = 0; index < Move.NumEdgeIndices(Board.Rows, Board.Columns); index++)
            {
                var move = Move.FromEdgeIndex(index, Board.Rows, Board.Columns);
                if (Board.IsMoveValid(move))
                {
                    m_ValidMoves[index] = true;
                    numValidMoves++;
                }
            }

            return numValidMoves > 0;
        }


        public override void Heuristic(in ActionBuffers actionsOut)
        {
            var discreteActions = actionsOut.DiscreteActions;
            discreteActions[0] = Board.GetRandomValidMoveIndex(m_Random);
        }
    }

}